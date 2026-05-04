import axios from 'axios';
import {
  SessionInfo,
  ChatRequest,
  ChatResponse,
  AvailableModelsResponse,
  SetModelRequest,
  SetModelResponse,
  GetSessionModelResponse
} from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
const API_PREFIX = `${API_BASE}/api`;

class APIService {
  async checkHealth(): Promise<{ status: string; agent: string; version: string }> {
    const response = await axios.get(`${API_PREFIX}/health`);
    return response.data;
  }

  async createSession(): Promise<{ session_id: string }> {
    const response = await axios.post(`${API_PREFIX}/session/new`);
    return response.data;
  }

  async getSessions(): Promise<{ sessions: SessionInfo[] }> {
    const response = await axios.get(`${API_PREFIX}/sessions`);
    return response.data;
  }

  async deleteSession(sessionId: string): Promise<{ success: boolean }> {
    const response = await axios.delete(`${API_PREFIX}/session/${sessionId}`);
    return response.data;
  }

  async clearChat(sessionId: string): Promise<ChatResponse> {
    const response = await axios.post(`${API_PREFIX}/clear`, null, {
      params: { session_id: sessionId }
    });
    return response.data;
  }

  async updateSessionName(sessionId: string, name: string): Promise<{ success: boolean; message: string }> {
    const response = await axios.put(`${API_PREFIX}/session/${sessionId}/name`, { name });
    return response.data;
  }

  async getAvailableModels(): Promise<AvailableModelsResponse> {
    const response = await axios.get(`${API_PREFIX}/models`);
    return response.data;
  }

  async setSessionModel(sessionId: string, modelId: string): Promise<SetModelResponse> {
    const response = await axios.put(
      `${API_PREFIX}/session/${sessionId}/model`,
      { model_id: modelId } as SetModelRequest
    );
    return response.data;
  }

  async getSessionModel(sessionId: string): Promise<GetSessionModelResponse> {
    const response = await axios.get(`${API_PREFIX}/session/${sessionId}/model`);
    return response.data;
  }

  async fetchStreamChat(request: ChatRequest, callbacks: {
    onChunk: (content: string) => void;
    onReasoning: (content: string) => void;
    onReasoningStart: () => void;
    onReasoningEnd: () => void;
    onAnswerStart: () => void;
    onMetadata: (data: { totalSteps: number; toolsUsed: string[]; hasReasoning: boolean; reasoningLength: number; answerLength: number }) => void;
    onError: (error: string) => void;
    onComplete: () => void;
    onStop?: () => boolean;
  }): Promise<void> {
    try {
      const response = await fetch(`${API_PREFIX}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorText = await response.text();
        callbacks.onError(`HTTP error! status: ${response.status} - ${errorText}`);
        return;
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        callbacks.onError('无法读取响应流');
        return;
      }

      while (true) {
        if (callbacks.onStop && callbacks.onStop()) {
          reader.cancel();
          break;
        }

        const { done, value } = await reader.read();

        if (done) {
          callbacks.onComplete();
          break;
        }

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6).trim();

            if (dataStr === '[DONE]') {
              callbacks.onComplete();
              return;
            }

            try {
              const data = JSON.parse(dataStr);
              const dataType = data.type;

              if (dataType === 'metadata') {
                callbacks.onMetadata({
                  totalSteps: data.total_steps || 0,
                  toolsUsed: data.tools_used || [],
                  hasReasoning: data.has_reasoning || false,
                  reasoningLength: data.reasoning_length || 0,
                  answerLength: data.answer_length || 0
                });
              } else if (dataType === 'reasoning_start') {
                callbacks.onReasoningStart();
              } else if (dataType === 'reasoning_chunk' && data.content) {
                callbacks.onReasoning(data.content + '\n');
              } else if (dataType === 'reasoning_end') {
                callbacks.onReasoningEnd();
              } else if (dataType === 'answer_start') {
                callbacks.onAnswerStart();
              } else if (dataType === 'chunk' && data.content) {
                callbacks.onChunk(data.content);
              } else if (dataType === 'error' && data.content) {
                callbacks.onError(data.content);
                return;
              } else if (dataType === 'done') {
                callbacks.onComplete();
                return;
              } else if (data.chunk) {
                callbacks.onChunk(data.chunk);
              } else if (data.error) {
                callbacks.onError(data.error);
                return;
              }
            } catch (e) {
              // 忽略JSON解析错误
            }
          }
        }
      }
    } catch (error) {
      console.error('[API] 网络错误:', error);
      callbacks.onError(error instanceof Error ? error.message : '网络错误');
    }
  }
}

export const apiService = new APIService();
