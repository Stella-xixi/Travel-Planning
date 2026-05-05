"""Chat API routes with SSE streaming."""
import asyncio
import json
from typing import AsyncGenerator, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import grpc
import sys
import os

from ..services.chat_service import ChatService
from ..dependencies.container import get_container

router = APIRouter()

# 全局变量
_grpc_stub = None
_agent_pb2 = None
_agent_pb2_grpc = None


def _ensure_proto_imported():
    """Ensure proto modules are imported."""
    global _agent_pb2, _agent_pb2_grpc, _grpc_stub
    if _agent_pb2 is None:
        # 添加 proto 路径
        proto_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'agent', 'proto'))
        if proto_path not in sys.path:
            sys.path.insert(0, proto_path)
        # 导入 proto 模块
        import agent_pb2
        import agent_pb2_grpc
        _agent_pb2 = agent_pb2
        _agent_pb2_grpc = agent_pb2_grpc


def init_grpc_stub(host: str = 'localhost', port: int = 50051):
    """Initialize gRPC stub."""
    global _grpc_stub
    if _grpc_stub is None:
        _ensure_proto_imported()
        channel = grpc.aio.insecure_channel(f'{host}:{port}')
        _grpc_stub = _agent_pb2_grpc.AgentServiceStub(channel)
    return _grpc_stub


def get_grpc_stub():
    """Get the gRPC stub."""
    global _grpc_stub
    if _grpc_stub is None:
        raise RuntimeError("gRPC stub not initialized. Call init_grpc_stub() first.")
    return _grpc_stub


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    session_id: Optional[str] = None


def get_chat_service() -> ChatService:
    """Get the chat service from the container."""
    container = get_container()
    return container.resolve('ChatService')


def get_session_service():
    """Get the session service from the container."""
    container = get_container()
    return container.resolve('SessionService')


async def generate_chat_stream(message: str, session_id: str) -> AsyncGenerator[str, None]:
    """Generate a chat response stream by calling the backend Agent gRPC service."""
    import logging
    logger = logging.getLogger(__name__)

    session_service = get_session_service()

    if not session_id:
        result = await session_service.create_session()
        session_id = result['session_id']

    yield f"data: {json.dumps({'type': 'session_id', 'session_id': session_id})}\n\n"
    yield f"data: {json.dumps({'type': 'reasoning_start'})}\n\n"

    try:
        # 确保 proto 已导入
        _ensure_proto_imported()

        # 获取 gRPC stub 并调用后端服务
        logger.info(f"[Chat] 通过 gRPC 调用 Agent 服务...")
        stub = get_grpc_stub()

        request = _agent_pb2.MessageRequest(
            session_id=session_id,
            user_input=message,
            model_id='',
            stream=False
        )

        # 调用 gRPC 服务
        response = await stub.ProcessMessage(request)

        logger.info(f"[Chat] gRPC 响应 success={response.success}")

        if response.success:
            # Yield reasoning 内容
            if response.reasoning.text:
                reasoning_text = response.reasoning.text
                # 分块发送 reasoning
                reasoning_chunks = reasoning_text.split('\n\n')
                for chunk in reasoning_chunks:
                    if chunk.strip():
                        yield f"data: {json.dumps({'type': 'reasoning_chunk', 'content': chunk.strip()})}\n\n"
                        await asyncio.sleep(0.1)

                yield f"data: {json.dumps({'type': 'reasoning_end'})}\n\n"
                yield f"data: {json.dumps({'type': 'answer_start'})}\n\n"

                # Stream answer chunks
                answer = response.answer
                for char in answer:
                    yield f"data: {json.dumps({'type': 'chunk', 'content': char})}\n\n"
                    await asyncio.sleep(0.01)
            else:
                # 如果没有 reasoning，直接返回 answer
                yield f"data: {json.dumps({'type': 'reasoning_end'})}\n\n"
                yield f"data: {json.dumps({'type': 'answer_start'})}\n\n"
                answer = response.answer
                for char in answer:
                    yield f"data: {json.dumps({'type': 'chunk', 'content': char})}\n\n"
                    await asyncio.sleep(0.01)
        else:
            # 处理失败
            error_msg = response.error or '处理失败'
            yield f"data: {json.dumps({'type': 'reasoning_chunk', 'content': f'处理出错: {error_msg}'})}\n\n"
            yield f"data: {json.dumps({'type': 'reasoning_end'})}\n\n"
            yield f"data: {json.dumps({'type': 'answer_start'})}\n\n"
            yield f"data: {json.dumps({'type': 'chunk', 'content': f'抱歉，处理您的请求时出现问题: {error_msg}'})}\n\n"

    except grpc.aio.AioRpcError as e:
        logger.error(f"[Chat] gRPC 调用失败: {e}")
        yield f"data: {json.dumps({'type': 'reasoning_chunk', 'content': f'连接后端服务失败: {str(e)}'})}\n\n"
        yield f"data: {json.dumps({'type': 'reasoning_end'})}\n\n"
        yield f"data: {json.dumps({'type': 'answer_start'})}\n\n"
        yield f"data: {json.dumps({'type': 'chunk', 'content': '抱歉，连接后端服务失败，请稍后重试。'})}\n\n"
    except Exception as e:
        logger.error(f"[Chat] 处理异常: {e}")
        yield f"data: {json.dumps({'type': 'reasoning_chunk', 'content': f'处理异常: {str(e)}'})}\n\n"
        yield f"data: {json.dumps({'type': 'reasoning_end'})}\n\n"
        yield f"data: {json.dumps({'type': 'answer_start'})}\n\n"
        yield f"data: {json.dumps({'type': 'chunk', 'content': f'抱歉，处理您的请求时出现异常。'})}\n\n"

    yield f"data: {json.dumps({'type': 'done'})}\n\n"


@router.post("/chat/stream")
async def stream_chat(request: ChatRequest):
    """
    Stream a chat response using Server-Sent Events.
    Calls the backend Agent gRPC service for intelligent responses.
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=422, detail="消息不能为空")

    return StreamingResponse(
        generate_chat_stream(request.message, request.session_id or ""),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
