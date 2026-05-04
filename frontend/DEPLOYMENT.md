# 小帅旅游助手 - Next.js 前端部署指南

> 本文档适用于 Next.js 前端版本的部署。

## 目录

- [快速开始](#快速开始)
- [本地开发](#本地开发)
- [生产环境部署](#生产环境部署)
- [Vercel 部署](#vercel-部署)
- [Netlify 部署](#netlify-部署)
- [环境变量配置](#环境变量配置)
- [常见问题](#常见问题)

---

## 快速开始

### 前置条件

- Node.js 18.x 或更高版本
- npm 9.x 或更高版本
- 后端服务运行中（默认 `http://localhost:8000`）

### 安装依赖

```bash
cd frontend
npm install
```

### 本地运行

```bash
npm run dev
```

访问 http://localhost:3000

---

## 本地开发

### 开发模式

```bash
npm run dev
```

- 支持热重载
- 自动打开浏览器

### 项目结构

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx          # 根布局
│   │   ├── page.tsx            # 首页
│   │   └── globals.css         # 全局样式
│   ├── components/             # React组件
│   │   ├── ChatArea.tsx        # 聊天交互区域
│   │   ├── MessageList.tsx     # 消息列表
│   │   └── Sidebar.tsx         # 侧边栏
│   ├── context/                # 状态管理
│   │   └── AppContext.tsx      # 全局Context
│   ├── services/               # API服务
│   │   └── api.ts              # 后端API调用
│   └── types/                  # TypeScript类型
│       └── index.ts            # 类型定义
├── package.json
├── next.config.js
├── tsconfig.json
└── DEPLOYMENT.md
```

### 构建预览

```bash
npm run build
npm start
```

---

## 生产环境部署

### 1. 构建应用

```bash
npm run build
```

### 2. 启动生产服务器

```bash
npm start
```

或使用 PM2 进程管理：

```bash
npm install -g pm2
pm2 start npm --name "shuai-travel" -- start
pm2 startup
pm2 save
```

---

## Vercel 部署

Vercel 是 Next.js 的官方推荐部署平台。

### 方式一：通过 Git 部署

1. 推送代码到 GitHub/GitLab/Bitbucket
2. 访问 [Vercel](https://vercel.com)
3. 导入项目
4. 配置环境变量：

```
NEXT_PUBLIC_API_BASE=http://your-backend-api.com
```

5. 点击 Deploy

### 方式二：通过 Vercel CLI

```bash
# 安装 Vercel CLI
npm i -g vercel

# 登录
vercel login

# 部署
cd frontend
vercel --prod
```

### Vercel 配置文件 (`vercel.json`)

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "installCommand": "npm install",
  "regions": ["iad1"],
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "${NEXT_PUBLIC_API_BASE}/api/:path*"
    }
  ]
}
```

---

## Netlify 部署

### 方式一：通过 Git 部署

1. 推送代码到 GitHub
2. 访问 [Netlify](https://netlify.com)
3. New site from Git
4. 选择仓库
5. 配置构建设置：

```
Build command: npm run build
Publish directory: .next
```

6. 添加环境变量
7. Deploy site

### 方式二：通过 Netlify CLI

```bash
# 安装 Netlify CLI
npm install -g netlify-cli

# 登录
netlify login

# 部署
cd frontend
netlify deploy --prod
```

### Netlify 配置文件 (`netlify.toml`)

```toml
[build]
  command = "npm run build"
  publish = ".next"

[build.environment]
  NODE_VERSION = "20"

[[redirects]]
  from = "/api/*"
  to = "http://your-backend-api.com/api/:splat"
  status = 200
```

---

## 环境变量配置

### 必需变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `NEXT_PUBLIC_API_BASE` | 后端 API 地址 | `http://localhost:8000` |

### 可选变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `NEXT_PUBLIC_APP_NAME` | 应用标题 | `小帅旅游助手` |
| `NEXT_TELEMETRY_DISABLE` | 禁用遥测 | `1` |

### 本地开发配置

创建 `.env.local` 文件：

```bash
# 后端 API 地址
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

### Vercel 环境变量

在 Vercel Dashboard → Settings → Environment Variables 中添加：

```
NEXT_PUBLIC_API_BASE = https://your-backend-api.com
```

---

## 常见问题

### Q1: 如何修改后端 API 地址？

在 `.env.local` 中设置：

```bash
NEXT_PUBLIC_API_BASE=http://your-backend:8000
```

### Q2: 部署后静态资源加载失败？

确保正确配置了 `output: 'standalone'` 在 `next.config.js`：

```javascript
module.exports = {
  output: 'standalone',
}
```

### Q3: 如何启用 HTTPS？

- **Vercel/Netlify**: 自动启用
- **其他平台**: 使用 Nginx 反向代理或平台提供的 SSL 证书

### Q4: 如何实现 API 代理？

在 `next.config.js` 中配置 rewrites：

```javascript
async rewrites() {
  return [
    {
      source: '/api/:path*',
      destination: `${process.env.NEXT_PUBLIC_API_BASE}/:path*`,
    },
  ]
},
```

### Q5: API 请求失败（CORS 错误）

**解决**：
1. 确保后端已配置 CORS
2. 检查后端服务是否运行
3. 配置 API 代理或使用完整 URL

### Q6: 流式响应不工作

**解决**：
1. 检查后端 `/api/chat/stream` 端点
2. 检查网络代理是否禁用了流式传输
3. Nginx 配置需添加 `proxy_buffering off`

---

## 性能优化建议

1. **启用缓存**：使用 `next/image` 优化图片
2. **代码分割**：Next.js 自动处理
3. **预取**：使用 `<Link prefetch={true}>`
4. **压缩**：启用 Gzip/Brotli
5. **CDN**：使用 Vercel Edge Network

---

## 相关链接

- [Next.js 文档](https://nextjs.org/docs)
- [Vercel 文档](https://vercel.com/docs)
- [Netlify 文档](https://docs.netlify.com)
- [React 文档](https://react.dev)

---

## 更新日志

### v2.0.0 (2024-12-27)
- ✅ 迁移到 Next.js 14 App Router
- ✅ 支持 SSR/SSG
- ✅ 优化构建配置
- ✅ 多平台部署文档
