'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Input, Button, Space, Card } from 'antd';
import { SendOutlined, StopOutlined, RobotOutlined } from '@ant-design/icons';
import { useAppContext } from '@/context/AppContext';
import { apiService } from '@/services/api';
import MessageList from './MessageList';

const { TextArea } = Input;

// 自定义 Hook：动态加载动画
const useLoadingDots = (isLoading: boolean) => {
  const [dots, setDots] = useState('');

  useEffect(() => {
    if (!isLoading) {
      setDots('');
      return;
    }

    const interval = setInterval(() => {
      setDots((prev) => {
        if (prev === '') return '.';
        if (prev === '.') return '..';
        if (prev === '..') return '...';
        return '';
      });
    }, 500);

    return () => clearInterval(interval);
  }, [isLoading]);

  return dots;
};

const ChatArea: React.FC = () => {
  const {
    currentSessionId,
    setCurrentSessionId,
    messages,
    addMessage,
    isStreaming,
    setIsStreaming,
    stopStreaming,
    setStopStreaming,
    refreshSessions,
  } = useAppContext();

  const [inputValue, setInputValue] = useState('');
  const [streamingMessage, setStreamingMessage] = useState('');
  const [streamingReasoning, setStreamingReasoning] = useState('');
  const [waitingForResponse, setWaitingForResponse] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [thinkingStartTime, setThinkingStartTime] = useState<number | null>(null);
  const [thinkingElapsed, setThinkingElapsed] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [reasoningExpanded, setReasoningExpanded] = useState<Record<string, boolean>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const loadingDots = useLoadingDots(waitingForResponse);

  // 思考计时器
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isThinking && thinkingStartTime) {
      interval = setInterval(() => {
        setThinkingElapsed(Math.floor((Date.now() - thinkingStartTime) / 1000));
      }, 1000);
    } else if (!isThinking) {
      setThinkingElapsed(0);
    }
    return () => clearInterval(interval);
  }, [isThinking, thinkingStartTime]);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingMessage, streamingReasoning, isThinking, waitingForResponse]);

  // 监听会话变化，重置所有流式状态
  useEffect(() => {
    setStreamingMessage('');
    setStreamingReasoning('');
    setWaitingForResponse(false);
    setIsThinking(false);
    setThinkingStartTime(null);
    setThinkingElapsed(0);
    setError(null);
    setIsStreaming(false);
    setStopStreaming(false);
  }, [currentSessionId]);

  const toggleReasoning = (messageId: string) => {
    setReasoningExpanded(prev => ({
      ...prev,
      [messageId]: !prev[messageId]
    }));
  };

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userMessageContent = inputValue.trim();
    const isFirstMessage = !currentSessionId || messages.length === 0;

    let sessionId = currentSessionId;
    if (!sessionId) {
      try {
        const data = await apiService.createSession();
        sessionId = data.session_id;
        setCurrentSessionId(sessionId);
      } catch (error) {
        console.error('创建会话失败:', error);
        return;
      }
    }

    const userMessage = {
      role: 'user' as const,
      content: inputValue,
      timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    };

    addMessage(userMessage);
    setInputValue('');
    setIsStreaming(true);
    setStopStreaming(false);
    setWaitingForResponse(true);
    setIsThinking(true);
    setThinkingStartTime(Date.now());
    setError(null);

    setStreamingMessage('');
    setStreamingReasoning('');

    // 设置会话名称
    if (isFirstMessage) {
      try {
        const sessionName = userMessageContent.slice(0, 15) + (userMessageContent.length > 15 ? '...' : '');
        await apiService.updateSessionName(sessionId, sessionName);
      } catch (error) {
        console.error('设置会话名称失败:', error);
      }
    }

    let fullResponse = '';
    let fullReasoning = '';
    let reasoningTimestamp = '';

    await apiService.fetchStreamChat(
      {
        message: userMessage.content,
        session_id: sessionId,
      },
      {
        onChunk: (content) => {
          fullResponse += content;
          setStreamingMessage((prev) => prev + content);
        },
        onReasoning: (content) => {
          fullReasoning += content;
          setStreamingReasoning((prev) => prev + content);
        },
        onReasoningStart: () => {
          setIsThinking(true);
          if (!thinkingStartTime) {
            setThinkingStartTime(Date.now());
          }
        },
        onReasoningTimestamp: (timestamp) => {
          reasoningTimestamp = timestamp;
        },
        onReasoningEnd: () => {
          setIsThinking(false);
        },
        onAnswerStart: () => {},
        onMetadata: () => {},
        onError: (errorMsg) => {
          setWaitingForResponse(false);
          setIsThinking(false);
          setError(errorMsg);
          fullResponse = `抱歉，出现错误：${errorMsg}`;
        },
        onComplete: () => {
          const finalReasoning = reasoningTimestamp ? `[Timestamp: ${reasoningTimestamp}]\n\n${fullReasoning}` : fullReasoning;
          const finalContent = fullResponse || streamingMessage;

          const finalMessage = {
            role: 'assistant' as const,
            content: finalContent,
            reasoning: finalReasoning,
            timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
          };

          addMessage(finalMessage);
          setStreamingMessage('');
          setStreamingReasoning('');
          setWaitingForResponse(false);
          setIsStreaming(false);
        },
        onStop: () => stopStreaming,
      }
    );

    refreshSessions();
  };

  const handleStop = () => {
    setStopStreaming(true);
    setWaitingForResponse(false);
    setIsThinking(false);
    setIsStreaming(false);

    if (streamingMessage || streamingReasoning) {
      const finalMessage = {
        role: 'assistant' as const,
        content: (streamingMessage || '已停止生成') + '\n\n⚠️ 已停止生成',
        reasoning: streamingReasoning,
        timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      };
      addMessage(finalMessage);
    }

    setStreamingMessage('');
    setStreamingReasoning('');
  };

  return (
    <div className="chat-input-area" style={{ display: 'flex', flexDirection: 'column', height: '100vh', padding: '24px' }}>
      <div className="chat-header" style={{ marginBottom: '16px' }}>
        <h2 style={{ margin: 0 }}>小帅旅游助手</h2>
        <p style={{ margin: '4px 0 0 0', color: '#666' }}>为您提供个性化的旅游推荐和路线规划</p>
      </div>

      <div style={{ flex: 1, overflow: 'auto', marginBottom: '16px' }}>
        <MessageList
          messages={messages}
          streamingReasoning={streamingReasoning}
          reasoningExpanded={reasoningExpanded}
          onToggleReasoning={toggleReasoning}
        />

        {isThinking && (
          <div style={{
            display: 'flex',
            justifyContent: 'flex-start',
            marginBottom: '16px',
            alignItems: 'flex-start',
            gap: '12px',
            maxWidth: '100%',
            padding: '0 16px',
          }}>
            {/* AI头像 */}
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              }}
            >
              <RobotOutlined style={{ color: 'white', fontSize: '18px' }} />
            </div>

            <div style={{ flex: 1, maxWidth: 'calc(100% - 52px)' }}>
              {/* 用户名 */}
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '6px', gap: '8px' }}>
                <span style={{ fontSize: '13px', fontWeight: 500, color: '#262730' }}>
                  小帅助手
                </span>
                <span style={{ fontSize: '11px', opacity: 0.6, color: '#999' }}>
                  Reasoning{loadingDots}
                </span>
              </div>

              {/* 思考中动画卡片 */}
              <Card
                style={{
                  background: '#fff',
                  borderRadius: '12px',
                  border: '1px solid #e8e8e8',
                }}
                bodyStyle={{ padding: '14px 16px' }}
              >
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '12px',
                  padding: '8px 0'
                }}>
                  {/* 脉冲动画圆点 */}
                  <div style={{ display: 'flex', gap: '6px' }}>
                    {[0, 1, 2].map((i) => (
                      <span
                        key={i}
                        style={{
                          display: 'inline-block',
                          width: '8px',
                          height: '8px',
                          borderRadius: '50%',
                          background: '#722ed1',
                          animation: `pulse 1.4s ease-in-out ${i * 0.2}s infinite`,
                        }}
                      />
                    ))}
                  </div>
                  <span style={{ fontSize: '13px', color: '#722ed1', fontWeight: 500 }}>
                    Deep Reasoning
                  </span>
                  <span style={{ fontSize: '13px', color: '#999' }}>
                    ({thinkingElapsed}s)
                  </span>
                </div>
              </Card>
            </div>
          </div>
        )}

        {error && (
          <div style={{ color: 'red', padding: '12px', background: '#fff2f0', borderRadius: '8px', marginBottom: '8px' }}>
            {error}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div>
        {!currentSessionId && messages.length === 0 && (
          <div style={{
            marginBottom: '16px',
            maxWidth: '100%'
          }}>
            {/* 欢迎提示 */}
            <div style={{
              textAlign: 'center',
              padding: '20px',
              background: 'linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%)',
              borderRadius: '12px',
              marginBottom: '16px'
            }}>
              <div style={{ fontSize: '16px', fontWeight: 600, color: '#262730', marginBottom: '8px' }}>
                欢迎使用小帅旅游助手
              </div>
              <div style={{ fontSize: '13px', color: '#666' }}>
                我可以帮您规划旅游路线、推荐景点、提供旅行建议等
              </div>
            </div>

            {/* 示例问题 */}
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '12px', color: '#999', marginBottom: '8px', textAlign: 'center' }}>
                试试这样问我：
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'center' }}>
                {[
                  '推荐一个周末短途旅行目的地',
                  '北京三日游怎么安排？',
                  '去云南旅游需要注意什么？',
                  '给我一个三亚自由行攻略'
                ].map((question, index) => (
                  <button
                    key={index}
                    onClick={() => setInputValue(question)}
                    style={{
                      padding: '8px 14px',
                      background: '#fff',
                      border: '1px solid #e8e8e8',
                      borderRadius: '20px',
                      fontSize: '13px',
                      color: '#262730',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = '#667eea';
                      e.currentTarget.style.background = '#f0f5ff';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = '#e8e8e8';
                      e.currentTarget.style.background = '#fff';
                    }}
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        <Space.Compact style={{ width: '100%' }}>
          <TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onPressEnter={(e) => {
              if (!e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder={isStreaming ? "正在生成回答中..." : "输入你的旅游需求..."}
            disabled={isStreaming}
            autoSize={{ minRows: 1, maxRows: 4 }}
            style={{ resize: 'none' }}
          />
          {isStreaming ? (
            <Button
              type="primary"
              danger
              icon={<StopOutlined />}
              onClick={handleStop}
            >
              停止
            </Button>
          ) : (
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSend}
              disabled={!inputValue.trim()}
            >
              发送
            </Button>
          )}
        </Space.Compact>
      </div>
    </div>
  );
};

export default ChatArea;
