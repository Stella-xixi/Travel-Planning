import { describe, it, expect, beforeEach } from 'vitest';
import { useChatStore } from '@/stores/chat';
import type { Message } from '@/types';

describe('ChatStore', () => {
  beforeEach(() => {
    // Reset state before each test using setState with initial values
    useChatStore.setState({
      messages: [],
      streamingMessage: '',
      streamingReasoning: '',
      isStreaming: false,
      isThinking: false,
      thinkingStartTime: null,
      thinkingElapsed: 0,
      error: null,
      reasoningExpanded: {},
    });
  });

  describe('addMessage', () => {
    it('should add a user message to the list', () => {
      const message: Message = {
        role: 'user',
        content: 'Hello',
        timestamp: '10:00',
      };

      useChatStore.getState().addMessage(message);

      expect(useChatStore.getState().messages).toHaveLength(1);
      expect(useChatStore.getState().messages[0]).toEqual(message);
    });

    it('should append messages to existing list', () => {
      const initialMessage: Message = {
        role: 'user',
        content: 'First',
        timestamp: '10:00',
      };

      const secondMessage: Message = {
        role: 'assistant',
        content: 'Hello!',
        timestamp: '10:01',
      };

      useChatStore.getState().addMessage(initialMessage);
      useChatStore.getState().addMessage(secondMessage);

      expect(useChatStore.getState().messages).toHaveLength(2);
    });
  });

  describe('streaming state', () => {
    it('should update streaming message', () => {
      useChatStore.getState().updateStreamingMessage('Hello');

      expect(useChatStore.getState().streamingMessage).toBe('Hello');

      useChatStore.getState().updateStreamingMessage(' World');

      expect(useChatStore.getState().streamingMessage).toBe('Hello World');
    });

    it('should update streaming reasoning', () => {
      useChatStore.getState().updateStreamingReasoning('Thinking...');

      expect(useChatStore.getState().streamingReasoning).toBe('Thinking...');
    });

    it('should toggle thinking state', () => {
      expect(useChatStore.getState().isThinking).toBe(false);

      useChatStore.getState().startThinking();

      expect(useChatStore.getState().isThinking).toBe(true);
      expect(useChatStore.getState().thinkingStartTime).not.toBeNull();

      useChatStore.getState().stopThinking();

      expect(useChatStore.getState().isThinking).toBe(false);
      expect(useChatStore.getState().thinkingStartTime).toBeNull();
    });
  });

  describe('setMessages', () => {
    it('should replace all messages', () => {
      const messages: Message[] = [
        { role: 'user', content: 'Hello', timestamp: '10:00' },
        { role: 'assistant', content: 'Hi!', timestamp: '10:01' },
      ];

      useChatStore.getState().setMessages(messages);

      expect(useChatStore.getState().messages).toHaveLength(2);
      expect(useChatStore.getState().messages).toEqual(messages);
    });
  });

  describe('clearMessages', () => {
    it('should clear all messages', () => {
      useChatStore.getState().addMessage({
        role: 'user',
        content: 'Test',
        timestamp: '10:00',
      });

      expect(useChatStore.getState().messages).toHaveLength(1);

      useChatStore.getState().clearMessages();

      expect(useChatStore.getState().messages).toHaveLength(0);
    });
  });

  describe('toggleReasoning', () => {
    it('should toggle reasoning expanded state', () => {
      expect(useChatStore.getState().reasoningExpanded['msg-1']).toBeUndefined();

      useChatStore.getState().toggleReasoning('msg-1');

      expect(useChatStore.getState().reasoningExpanded['msg-1']).toBe(true);

      useChatStore.getState().toggleReasoning('msg-1');

      expect(useChatStore.getState().reasoningExpanded['msg-1']).toBe(false);
    });
  });

  describe('setError', () => {
    it('should set error message', () => {
      expect(useChatStore.getState().error).toBeNull();

      useChatStore.getState().setError('Something went wrong');

      expect(useChatStore.getState().error).toBe('Something went wrong');
    });

    it('should clear error when set to null', () => {
      useChatStore.getState().setError('Error');
      expect(useChatStore.getState().error).toBe('Error');

      useChatStore.getState().setError(null);
      expect(useChatStore.getState().error).toBeNull();
    });
  });

  describe('reset', () => {
    it('should reset all state to initial values', () => {
      useChatStore.getState().addMessage({
        role: 'user',
        content: 'test',
        timestamp: '10:00',
      });
      useChatStore.getState().startThinking();
      useChatStore.getState().updateStreamingMessage('streaming');
      useChatStore.getState().setError('error');

      useChatStore.getState().reset();

      expect(useChatStore.getState().messages).toHaveLength(0);
      expect(useChatStore.getState().streamingMessage).toBe('');
      expect(useChatStore.getState().isThinking).toBe(false);
      expect(useChatStore.getState().isStreaming).toBe(false);
      expect(useChatStore.getState().error).toBeNull();
    });
  });
});
