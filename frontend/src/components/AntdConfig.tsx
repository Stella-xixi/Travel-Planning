'use client';

import React from 'react';
import { ConfigProvider } from 'antd';

const AntdConfig: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#1890ff',
          borderRadius: 6,
        },
      }}
    >
      {children}
    </ConfigProvider>
  );
};

export default AntdConfig;
