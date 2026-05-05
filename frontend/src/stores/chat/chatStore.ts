import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { Message } from '@/types';

interface ChatState {
  // 消息列表
  messages: Message[];

  // 流式响应临时状态
  streamingMessage: string;
  streamingReasoning: string;
  isStreaming: boolean;

  // 思考过程状态
  isThinking: boolean;
  thinkingStartTime: number | null;
  thinkingElapsed: number;

  // 错误状态
  error: string | null;

  // 思考展开状态
  reasoningExpanded: Record<string, boolean>;

  // Actions
  addMessage: (message: Message) => void;
  setMessages: (messages: Message[]) => void;
  clearMessages: () => void;
  updateStreamingMessage: (content: string) => void;
  updateStreamingReasoning: (content: string) => void;
  setStreaming: (streaming: boolean) => void;
  startThinking: () => void;
  stopThinking: () => void;
  updateThinkingElapsed: (elapsed: number) => void;
  setError: (error: string | null) => void;
  toggleReasoning: (messageId: string) => void;
  reset: () => void;
  resetStreamingState: () => void;
}

const initialState = {
  messages: [],
  streamingMessage: '',
  streamingReasoning: '',
  isStreaming: false,
  isThinking: false,
  thinkingStartTime: null,
  thinkingElapsed: 0,
  error: null,
  reasoningExpanded: {},
};

export const useChatStore = create<ChatState>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        addMessage: (message) =>
          set(
            (state) => ({
              messages: [...state.messages, message],
            }),
            false,
            'chat/addMessage'
          ),

        setMessages: (messages) =>
          set({ messages }, false, 'chat/setMessages'),

        clearMessages: () =>
          set({ messages: [] }, false, 'chat/clearMessages'),

        updateStreamingMessage: (content) =>
          set(
            (state) => ({
              streamingMessage: state.streamingMessage + content,
            }),
            false,
            'chat/updateStreamingMessage'
          ),

        updateStreamingReasoning: (content) =>
          set(
            (state) => ({
              streamingReasoning: state.streamingReasoning + content,
            }),
            false,
            'chat/updateStreamingReasoning'
          ),

        setStreaming: (streaming) =>
          set({ isStreaming: streaming }, false, 'chat/setStreaming'),

        startThinking: () =>
          set(
            {
              isThinking: true,
              thinkingStartTime: Date.now(),
              thinkingElapsed: 0,
            },
            false,
            'chat/startThinking'
          ),

        stopThinking: () =>
          set(
            {
              isThinking: false,
              thinkingStartTime: null,
              thinkingElapsed: 0,
            },
            false,
            'chat/stopThinking'
          ),

        updateThinkingElapsed: (elapsed) =>
          set({ thinkingElapsed: elapsed }, false, 'chat/updateThinkingElapsed'),

        setError: (error) =>
          set({ error }, false, 'chat/setError'),

        toggleReasoning: (messageId) =>
          set(
            (state) => ({
              reasoningExpanded: {
                ...state.reasoningExpanded,
                [messageId]: !state.reasoningExpanded[messageId],
              },
            }),
            false,
            'chat/toggleReasoning'
          ),

        reset: () => set(initialState, false, 'chat/reset'),

        resetStreamingState: () =>
          set(
            {
              streamingMessage: '',
              streamingReasoning: '',
              isStreaming: false,
              isThinking: false,
              thinkingStartTime: null,
              thinkingElapsed: 0,
              error: null,
            },
            false,
            'chat/resetStreamingState'
          ),
      }),
      {
        name: 'chat-storage',
        partialize: (state) => ({
          messages: state.messages,
        }),
      }
    ),
    { name: 'ChatStore' }
  )
);
