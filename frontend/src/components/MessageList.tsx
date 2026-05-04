'use client';

import React from 'react';
import { Card } from 'antd';
import { Message } from '@/types';
import ReactMarkdown from 'react-markdown';
import type { Components } from 'react-markdown';
import { BulbOutlined, DownOutlined, UpOutlined } from '@ant-design/icons';

interface Props {
  messages: Message[];
  streamingMessage?: string;
  isThinking?: boolean;
  reasoningExpanded?: Record<string, boolean>;
  onToggleReasoning?: (messageId: string) => void;
}

const cleanContent = (content: string): string => {
  if (!content) return '';
  return content
    .replace(/\n{2,}/g, '\n')
    .replace(/[ \t]+$/gm, '')
    .trim();
};

const markdownComponents: Components = {
  p: ({ children }) => <p style={{ margin: 0, padding: 0 }}>{children}</p>,
  li: ({ children }) => <li style={{ margin: 0, padding: 0, lineHeight: 1.6 }}>{children}</li>,
  h1: ({ children }) => <h1 style={{ margin: '4px 0 2px 0', fontSize: '1.5em', fontWeight: 600 }}>{children}</h1>,
  h2: ({ children }) => <h2 style={{ margin: '4px 0 2px 0', fontSize: '1.3em', fontWeight: 600 }}>{children}</h2>,
  h3: ({ children }) => <h3 style={{ margin: '4px 0 2px 0', fontSize: '1.1em', fontWeight: 600 }}>{children}</h3>,
  ol: ({ children }) => <ol style={{ margin: '2px 0', paddingLeft: '20px' }}>{children}</ol>,
  ul: ({ children }) => <ul style={{ margin: '2px 0', paddingLeft: '20px' }}>{children}</ul>,
};

interface ReasoningBlockProps {
  reasoning: string;
  messageId: string;
  isExpanded: boolean;
  onToggle: (messageId: string) => void;
  isStreaming?: boolean;
}

const ReasoningBlock: React.FC<ReasoningBlockProps> = ({
  reasoning,
  messageId,
  isExpanded,
  onToggle,
  isStreaming = false
}) => {
  if (!reasoning) return null;

  return (
    <div
      style={{
        marginBottom: '8px',
        background: '#fafafa',
        borderRadius: '8px',
        border: '1px solid #e8e8e8',
        overflow: 'hidden'
      }}
    >
      <div
        onClick={() => onToggle(messageId)}
        style={{
          display: 'flex',
          alignItems: 'center',
          padding: '8px 12px',
          cursor: 'pointer',
          background: '#f5f5f5',
          borderBottom: isExpanded ? '1px solid #e8e8e8' : 'none',
          userSelect: 'none'
        }}
      >
        <BulbOutlined
          style={{
            color: isStreaming ? '#722ed1' : '#52c41a',
            marginRight: '8px',
            fontSize: '14px'
          }}
        />
        <span style={{ fontSize: '13px', color: '#666', flex: 1 }}>
          {isStreaming ? '思考中...' : '深度思考'}
        </span>
        {isExpanded ? (
          <UpOutlined style={{ color: '#999', fontSize: '12px' }} />
        ) : (
          <DownOutlined style={{ color: '#999', fontSize: '12px' }} />
        )}
      </div>

      {isExpanded && (
        <div
          style={{
            padding: '12px',
            background: '#fff',
            fontFamily: 'monospace',
            fontSize: '12px',
            lineHeight: '1.7',
            whiteSpace: 'pre-wrap',
            maxHeight: '300px',
            overflow: 'auto'
          }}
        >
          <ReactMarkdown components={markdownComponents}>
            {cleanContent(reasoning)}
          </ReactMarkdown>
        </div>
      )}
    </div>
  );
};

const MessageItem: React.FC<{
  msg: Message;
  reasoningExpanded: Record<string, boolean>;
  onToggleReasoning: (messageId: string) => void;
}> = ({ msg, reasoningExpanded, onToggleReasoning }) => {
  const isUser = msg.role === 'user';
  const messageId = `msg_${msg.timestamp}_${msg.content.slice(0, 10)}`;
  const isExpanded = reasoningExpanded[messageId] ?? false;

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        marginBottom: '8px'
      }}
    >
      <Card
        style={{
          width: '100%',
          background: isUser
            ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
            : '#fff',
          color: isUser ? 'white' : '#262730',
          borderRadius: '12px',
          border: isUser ? 'none' : '1px solid #e8e8e8',
        }}
        bodyStyle={{ padding: '16px' }}
      >
        <div style={{
          fontSize: '13px',
          marginBottom: '8px',
          opacity: 0.8,
          fontWeight: 500
        }}>
          {isUser ? '你' : '小帅助手'}
        </div>

        {!isUser && msg.reasoning && (
          <ReasoningBlock
            reasoning={msg.reasoning}
            messageId={messageId}
            isExpanded={isExpanded}
            onToggle={onToggleReasoning}
          />
        )}

        <div style={{ lineHeight: 1.7 }}>
          <ReactMarkdown components={markdownComponents}>
            {cleanContent(msg.content)}
          </ReactMarkdown>
        </div>

        <div style={{
          fontSize: '11px',
          marginTop: '8px',
          opacity: 0.6,
          textAlign: 'right'
        }}>
          {msg.timestamp}
        </div>
      </Card>
    </div>
  );
};

const MessageList: React.FC<Props> = ({
  messages,
  streamingMessage,
  reasoningExpanded = {},
  onToggleReasoning
}) => {
  return (
    <div style={{ maxWidth: '900px', margin: '0 auto', width: '100%' }}>
      {messages.map((msg, index) => (
        <MessageItem
          key={index}
          msg={msg}
          reasoningExpanded={reasoningExpanded}
          onToggleReasoning={onToggleReasoning || (() => {})}
        />
      ))}

      {streamingMessage && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            marginBottom: '8px'
          }}
        >
          <Card
            style={{
              width: '100%',
              background: '#fff',
              borderRadius: '12px',
              border: '1px solid #e8e8e8',
            }}
            bodyStyle={{ padding: '16px' }}
          >
            <div style={{ fontSize: '13px', color: '#666', marginBottom: '8px', fontWeight: 500 }}>
              小帅助手
            </div>
            <div style={{ lineHeight: 1.7 }}>
              <ReactMarkdown components={markdownComponents}>
                {cleanContent(streamingMessage)}
              </ReactMarkdown>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

export default MessageList;
