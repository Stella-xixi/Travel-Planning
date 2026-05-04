'use client';

import { Layout } from 'antd';
import ChatArea from '@/components/ChatArea';
import Sidebar from '@/components/Sidebar';

export default function Home() {
  // 侧边栏始终显示，只是空会话时不显示内容
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Layout.Sider
        width={280}
        theme="light"
        style={{
          borderRight: '1px solid #f0f0f0',
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          zIndex: 100,
        }}
      >
        <Sidebar />
      </Layout.Sider>
      <Layout style={{ marginLeft: 280, transition: 'margin-left 0.2s' }}>
        <Layout.Content style={{ margin: 0, minHeight: '100vh' }}>
          <ChatArea />
        </Layout.Content>
      </Layout>
    </Layout>
  );
}
