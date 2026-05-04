'use client';

import React, { useState, useEffect } from 'react';
import { Card, Timeline, Tag, Spin } from 'antd';
import { CheckCircleOutlined, ClockCircleOutlined, SyncOutlined, RobotOutlined } from '@ant-design/icons';
import { useAppContext } from '@/context/AppContext';

interface Step {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  timestamp: string;
  description?: string;
}

const TaskSteps: React.FC = () => {
  const { currentSessionId, messages } = useAppContext();
  const [steps, setSteps] = useState<Step[]>([]);
  const [loading, setLoading] = useState(false);

  // 根据消息生成步骤
  useEffect(() => {
    if (messages.length > 0) {
      generateStepsFromMessages();
    } else {
      setSteps([]);
    }
  }, [messages]);

  const generateStepsFromMessages = () => {
    const newSteps: Step[] = [];
    const userMessages = messages.filter((m: any) => m.role === 'user');
    const assistantMessages = messages.filter((m: any) => m.role === 'assistant');

    // 添加用户提问步骤
    userMessages.forEach((msg: any, index: number) => {
      newSteps.push({
        id: `user-${index}`,
        name: '用户提问',
        status: 'completed',
        timestamp: msg.timestamp,
        description: msg.content.slice(0, 50) + (msg.content.length > 50 ? '...' : ''),
      });
    });

    // 添加助手回答步骤（从 reasoning 中提取）
    assistantMessages.forEach((msg: any, index: number) => {
      if (msg.reasoning && msg.reasoning.trim()) {
        // 解析 reasoning 内容生成步骤
        const reasoningLines = msg.reasoning.split('\n').filter((line: string) => line.trim());
        reasoningLines.forEach((line: string, lineIndex: number) => {
          newSteps.push({
            id: `step-${index}-${lineIndex}`,
            name: `执行步骤 ${index + 1}.${lineIndex + 1}`,
            status: 'completed',
            timestamp: msg.timestamp,
            description: line.trim().slice(0, 100),
          });
        });
      }

      // 添加最终回答步骤
      newSteps.push({
        id: `answer-${index}`,
        name: '生成回答',
        status: 'completed',
        timestamp: msg.timestamp,
        description: msg.content.slice(0, 80) + (msg.content.length > 80 ? '...' : ''),
      });
    });

    setSteps(newSteps);
  };

  if (!currentSessionId || messages.length === 0) {
    return null;
  }

  return (
    <div style={{
      height: 180,
      borderBottom: '1px solid #f0f0f0',
      padding: '16px 24px',
      background: '#fafafa',
      overflow: 'auto',
    }}>
      <div style={{ marginBottom: 12 }}>
        <RobotOutlined style={{ marginRight: 8, color: '#722ed1' }} />
        <span style={{ fontWeight: 500, color: '#1a1a1a' }}>任务执行步骤</span>
        <Tag color="purple" style={{ marginLeft: 8 }}>{steps.length} 步</Tag>
      </div>

      {steps.length > 0 ? (
        <div style={{
          display: 'flex',
          gap: 8,
          overflowX: 'auto',
          paddingBottom: 4,
        }}>
          {steps.map((step, index) => (
            <div
              key={step.id}
              style={{
                flexShrink: 0,
                padding: '8px 12px',
                background: '#fff',
                borderRadius: 8,
                border: '1px solid #f0f0f0',
                maxWidth: 200,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 12 }} />
                <span style={{ fontSize: 12, fontWeight: 500, color: '#1a1a1a' }}>
                  {step.name}
                </span>
              </div>
              <div style={{
                fontSize: 11,
                color: '#999',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}>
                {step.description}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div style={{ color: '#999', fontSize: 13 }}>
          <SyncOutlined spin style={{ marginRight: 8 }} />
          等待任务执行...
        </div>
      )}
    </div>
  );
};

export default TaskSteps;
