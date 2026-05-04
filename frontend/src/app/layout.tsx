import type { Metadata } from 'next';
import './globals.css';
import { AppProvider } from '@/context/AppContext';
import AntdConfig from '@/components/AntdConfig';

export const metadata: Metadata = {
  title: '小帅旅游助手 - 智能AI旅游推荐系统',
  description: '基于自定义ReAct Agent架构的智能旅游助手系统，提供城市推荐、景点查询、路线规划等功能',
  keywords: ['旅游', 'AI助手', 'ReAct Agent', '旅游推荐', '路线规划'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body>
        <AntdConfig>
          <AppProvider>
            {children}
          </AppProvider>
        </AntdConfig>
      </body>
    </html>
  );
}
