"""
gRPC 服务器
"""

import sys
import os
import grpc
from concurrent import futures
import json
import logging
from typing import Iterator

# 添加 proto 路径
PROTO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'proto')
if PROTO_PATH not in sys.path:
    sys.path.insert(0, PROTO_PATH)

from proto import agent_pb2, agent_pb2_grpc

from .core.travel_planning_agent_runtime import ReActTravelAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentServicer:
    """Agent 服务实现"""

    def __init__(self, config_path: str = "config/llm_config.yaml"):
        self.agent = ReActTravelAgent(config_path=config_path)
        logger.info("Agent 服务已初始化")

    def ProcessMessage(self, request, context):
        """处理消息（非流式）"""
        try:
            result = self.agent.process_sync(request.user_input)
            return self._build_response(result, context)
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return self._build_error_response(str(e), context)

    def StreamMessage(self, request, context) -> Iterator:
        """处理消息（流式）"""
        try:
            user_input = request.user_input
            agent = self.agent

            # 添加用户消息
            agent.memory_manager.add_message('user', user_input)

            # 执行推理
            result = agent.react_agent.run(user_input, {
                'user_query': user_input,
                'user_preference': agent.memory_manager.get_user_preference()
            })

            history = result.get('history', [])

            # 发送思考过程
            reasoning_text = agent._build_reasoning_text(history)
            yield agent_pb2.StreamChunk(chunk_type="thinking", content=reasoning_text, is_last=False)

            # 发送答案
            answer = agent._extract_answer(history)
            yield agent_pb2.StreamChunk(chunk_type="answer", content=answer, is_last=False)

            # 发送完成信号
            yield agent_pb2.StreamChunk(chunk_type="done", content="", is_last=True)

        except Exception as e:
            logger.error(f"流式处理失败: {e}")
            yield agent_pb2.StreamChunk(chunk_type="error", content=str(e), is_last=True)

    def HealthCheck(self, request, context):
        """健康检查"""
        return agent_pb2.HealthResponse(healthy=True, version="1.0.0", status="running")

    def _build_response(self, result, context):
        """构建响应"""
        if result.get("success", False):
            reasoning = result.get("reasoning", {})
            history = result.get("history", [])
            return agent_pb2.MessageResponse(
                success=True,
                answer=result.get("answer", ""),
                reasoning=agent_pb2.ReasoningInfo(
                    text=reasoning.get("text", ""),
                    total_steps=reasoning.get("total_steps", 0),
                    tools_used=reasoning.get("tools_used", [])
                ),
                history=[
                    agent_pb2.HistoryStep(
                        step=step.get("step", 0),
                        thought=agent_pb2.ThoughtInfo(
                            id=step.get("thought", {}).get("id", ""),
                            type=step.get("thought", {}).get("type", ""),
                            content=step.get("thought", {}).get("content", ""),
                            confidence=step.get("thought", {}).get("confidence", 0.0),
                            decision=step.get("thought", {}).get("decision", "")
                        ),
                        action=agent_pb2.ActionInfo(
                            id=step.get("action", {}).get("id", ""),
                            tool_name=step.get("action", {}).get("tool_name", ""),
                            status=step.get("action", {}).get("status", ""),
                            duration=step.get("action", {}).get("duration", 0)
                        ),
                        evaluation=agent_pb2.EvaluationInfo(
                            success=step.get("evaluation", {}).get("success", False),
                            duration=step.get("evaluation", {}).get("duration", 0)
                        )
                    )
                    for step in history
                ]
            )
        else:
            return agent_pb2.MessageResponse(
                success=False,
                error=result.get("error", "未知错误")
            )

    def _build_error_response(self, error: str, context):
        """构建错误响应"""
        return agent_pb2.MessageResponse(
            success=False,
            error=error
        )


def serve(config_path: str = "config/config.json", port: int = 50051):
    """启动 gRPC 服务器"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # 添加服务
    agent_servicer = AgentServicer(config_path)
    # 注册 gRPC 服务
    agent_pb2_grpc.add_AgentServiceServicer_to_server(agent_servicer, server)

    server.add_insecure_port(f'[::]:{port}')
    server.start()

    logger.info(f"Agent gRPC 服务器已启动，端口: {port}")
    return server


if __name__ == '__main__':
    import argparse

    # Get project root (parent of agent/)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    parser = argparse.ArgumentParser(description='ShuaiTravelAgent gRPC Server')
    parser.add_argument('--config', type=str,
                        default=os.path.join(project_root, 'config', 'llm_config.yaml'),
                        help='Path to config file')
    parser.add_argument('--port', type=int, default=50051,
                        help='Port to listen on')
    args = parser.parse_args()

    config_path = args.config

    print(f"[*] Starting Agent gRPC Server...")
    print(f"    Config: {config_path}")
    print(f"    Port: {args.port}")
    print()

    server = serve(config_path, args.port)
    print(f"[OK] Agent gRPC Server started on port {args.port}")
    print("    Press Ctrl+C to stop")
    server.wait_for_termination()
