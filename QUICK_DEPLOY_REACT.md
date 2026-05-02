# React前端快速部署启动指南

## 📋 目录
- [前置条件](#前置条件)
- [快速启动](#快速启动)
- [开发环境配置](#开发环境配置)
- [生产构建与部署](#生产构建与部署)
- [前后端集成](#前后端集成)
- [常见问题](#常见问题)

---

## 前置条件

### 系统要求
- **Node.js** >= 16.0.0
- **npm** >= 8.0.0
- **Python** >= 3.8（后端）
- **Windows/Mac/Linux** 任意操作系统

### 环境检查
```bash
# 检查Node.js版本
node --version

# 检查npm版本
npm --version

# 检查Python版本
python --version
```

### 配置文件准备
确保项目根目录下已有 `config/config.json`，包含LLM API配置：
```json
{
  "llm": {
    "provider_type": "openai",
    "api_key": "YOUR_API_KEY_HERE",
    "model": "gpt-4o-mini"
  },
  "web": {
    "host": "0.0.0.0",
    "port": 8000
  }
}
```

---

## 快速启动

### 一分钟快速启动

#### 步骤1：启动后端API（需要一个终端）
```bash
python run_api.py
```

等待显示：
```
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### 步骤2：启动React前端（需要另一个终端）
```bash
cd frontend
npm install    # 首次运行需要（~2-3分钟）
npm run dev
```

等待显示：
```
VITE v5.0.8  ready in XXX ms

  ➜  Local:   http://localhost:3000/
```

#### 步骤3：访问应用
打开浏览器访问：**http://localhost:3000**

---

## 开发环境配置

### 完整开发环境设置

#### 后端环境
```bash
# 1. 确保Python环境已激活（如使用虚拟环境）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 2. 安装后端依赖
pip install -r requirements.txt

# 3. 验证配置文件
ls config/config.json  # 确保文件存在

# 4. 启动后端服务
python run_api.py
```

#### 前端环境
```bash
# 1. 进入frontend目录
cd frontend

# 2. 安装npm依赖
npm install

# 3. 启动开发服务器
npm run dev

# 4. 浏览器自动打开 http://localhost:3000
```

### 开发常用命令

**前端开发命令**：
```bash
cd frontend

npm run dev       # 启动开发服务器（支持热更新）
npm run build     # 生产环境构建
npm run preview   # 预览生产构建
npm run lint      # 代码检查
```

**后端开发命令**：
```bash
python run_api.py              # 启动API服务
python run_streamlit.py        # 启动Streamlit界面（可选）
```

### 工作流程

1. **日常开发**
   - 保持后端服务运行：`python run_api.py`
   - 保持前端开发服务器运行：`npm run dev`
   - 修改代码后自动热更新
   - 打开http://localhost:3000测试

2. **调试API**
   - 后端API文档：http://localhost:8000/docs
   - 可直接在Swagger UI中测试各个端点

3. **检查日志**
   - 后端日志：查看 `python run_api.py` 运行窗口
   - 前端日志：查看浏览器开发者工具（F12）

---

## 生产构建与部署

### 生产环境构建

#### 构建前端静态资源
```bash
cd frontend

# 1. 安装依赖（如果还没有）
npm install

# 2. 执行生产构建
npm run build

# 3. 查看构建产物
ls dist/  # 应包含 index.html 和 assets 目录
```

#### 构建产物说明
```
dist/
├── index.html                    # 入口HTML文件
├── assets/
│   ├── index-[hash].js          # 打包后的JavaScript
│   ├── index-[hash].css         # 打包后的CSS样式
│   └── vendor-[hash].js         # 第三方库代码
└── vite.svg                      # 静态资源
```

### 部署方案

#### 方案1：Nginx部署（推荐）

**1. 配置Nginx**
```nginx
server {
    listen 80;
    server_name yourdomain.com;  # 修改为您的域名
    
    # 前端静态文件
    location / {
        root /var/www/shuai-travel-agent/frontend/dist;
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "public, max-age=31536000" always;
    }
    
    # API代理
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }
}
```

**2. 部署步骤**
```bash
# 上传构建产物
scp -r dist/ user@server:/var/www/shuai-travel-agent/frontend/

# 启用Nginx配置
sudo nginx -s reload

# 启动后端服务
ssh user@server
cd /var/www/shuai-travel-agent
python run_api.py &
```

#### 方案2：使用FastAPI托管前端

**修改后端配置**（可选）：
```python
# 在 src/shuai_travel_planning_agent_runtime/app.py 中添加
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# 托管前端
frontend_dist = os.path.join("frontend", "dist")
if os.path.exists(frontend_dist):
    @app.get("/")
    async def serve_frontend():
        return FileResponse(os.path.join(frontend_dist, "index.html"))
    
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")))
```

**启动命令**：
```bash
# 1. 构建前端
cd frontend && npm run build && cd ..

# 2. 启动后端（会自动托管前端）
python run_api.py

# 访问：http://localhost:8000
```

#### 方案3：容器化部署（Docker）

**构建Docker镜像**：
```bash
# 在项目根目录创建 Dockerfile
docker build -t shuai-travel-agent .

# 运行容器
docker run -p 8000:8000 -p 3000:3000 shuai-travel-agent
```

---

## 前后端集成

### API集成说明

**后端API基础地址**：
- 开发环境：`http://localhost:8000`
- 生产环境：根据部署地址更改

**前端API配置**：
```typescript
// 开发环境：src/services/api.ts
const API_BASE = '/api';  // 通过Vite代理转发

// 生产环境：自动使用部署地址
```

### 关键API端点

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/chat` | 普通聊天 |
| POST | `/api/chat/stream` | 流式聊天（SSE） |
| POST | `/api/session/new` | 创建新会话 |
| GET | `/api/sessions` | 获取会话列表 |
| DELETE | `/api/session/{id}` | 删除会话 |
| POST | `/api/clear` | 清空对话 |
| GET | `/api/health` | 健康检查 |

### 测试集成

**1. 检查后端健康状态**
```bash
curl http://localhost:8000/api/health
# 应返回：{"status":"healthy","agent":"TravelAssistantAgent","version":"1.0.0"}
```

**2. 在前端测试**
- 打开 http://localhost:3000
- 点击"新建会话"
- 输入消息并发送
- 应看到流式AI回复

---

## 常见问题

### Q1: npm install 失败

**症状**：
```
npm ERR! code ERESOLVE
npm ERR! ERESOLVE unable to resolve dependency tree
```

**解决方案**：
```bash
# 清除缓存
npm cache clean --force

# 重新安装
cd frontend
rm -rf node_modules package-lock.json
npm install

# 或使用国内镜像
npm config set registry https://registry.npmmirror.com
npm install
```

---

### Q2: React前端无法连接后端API

**症状**：
- 页面能打开但无法发送消息
- 浏览器控制台显示CORS错误
- Network标签显示API请求失败

**检查步骤**：
```bash
# 1. 确认后端服务正常运行
curl http://localhost:8000/api/health

# 2. 查看后端日志确认CORS配置
# 应看到 CORSMiddleware 相关日志

# 3. 检查前端API配置
# frontend/src/services/api.ts 中 API_BASE 应为 '/api'

# 4. 查看浏览器Network标签
# 请求URL应为 http://localhost:3000/api/...
```

**解决方案**：
```bash
# 重启两个服务
# 终端1
python run_api.py

# 终端2（新开）
cd frontend
npm run dev
```

---

### Q3: 前端页面空白或显示错误

**症状**：
- 浏览器白屏
- 控制台有JavaScript错误

**调试方法**：
```bash
# 1. 打开浏览器开发者工具（F12）
# 2. 查看 Console 标签中的错误信息
# 3. 查看 Network 标签确认文件是否加载

# 常见错误原因：
# - node_modules 未安装：运行 npm install
# - Vite配置错误：检查 vite.config.ts
# - API代理配置错误：确认后端运行在8000端口
```

**重新构建**：
```bash
cd frontend
rm -rf node_modules dist
npm install
npm run dev
```

---

### Q4: 构建后体积过大

**症状**：
```
dist/assets/ 文件总大小 > 2MB
```

**优化方案**：
```bash
# 1. 分析构建体积
npm run build -- --mode production

# 2. 查看依赖大小
npm list --depth=0

# 3. 移除未使用的依赖
npm prune
npm install
```

---

### Q5: 流式响应不工作

**症状**：
- AI回复不显示
- 显示"正在思考中..."但无进展
- Network标签显示流式响应挂起

**检查步骤**：
```bash
# 1. 测试SSE端点
curl -N http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"你好","session_id":"test"}'

# 2. 检查后端LLM配置
# 确保 config/config.json 中 api_key 有效

# 3. 查看后端日志
# 应看到 LLM 调用相关日志

# 4. 检查前端代码
# frontend/src/services/api.ts fetchStreamChat 方法
```

**解决方案**：
```bash
# 重启后端并检查日志
python run_api.py

# 在前端尝试简单消息
# 例如："你好" 而不是复杂查询
```

---

### Q6: 后端启动失败

**症状**：
```
ModuleNotFoundError: No module named 'fastapi'
或
FileNotFoundError: config/config.json not found
```

**解决方案**：
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 检查配置文件
ls config/config.json

# 3. 确保在项目根目录启动
cd /path/to/ShuaiTravelAgent
python run_api.py
```

---

### Q7: 端口已被占用

**症状**：
```
[ERROR] Address already in use: ('0.0.0.0', 8000)
或
ERROR in http://localhost:3000 - EADDRINUSE: address already in use
```

**解决方案**：
```bash
# Windows - 查找占用端口的进程
netstat -ano | findstr :8000
taskkill /PID [PID] /F

# Linux/Mac - 杀死占用端口的进程
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

---

### Q8: 修改代码后前端不更新

**症状**：
- 修改React组件代码
- 页面未自动刷新
- 需要手动刷新浏览器

**检查项**：
```bash
# 1. 确认 npm run dev 仍在运行
# 终端应显示 "ready in" 消息

# 2. 查看文件是否正确保存
# 检查文件修改时间

# 3. 检查Vite配置
# vite.config.ts 中应启用HMR

# 4. 重启开发服务器
cd frontend
npm run dev
```

---

## 验收清单

启动成功的标志：

- ✅ 后端：`python run_api.py` 输出 "Uvicorn running on http://0.0.0.0:8000"
- ✅ 前端：`npm run dev` 输出 "Local: http://localhost:3000/"
- ✅ 浏览器能访问 http://localhost:3000
- ✅ 页面显示"小帅旅游助手"标题
- ✅ 能创建会话并发送消息
- ✅ AI能正常回复（流式显示）
- ✅ 能看到"🤔 正在思考中..."提示
- ✅ 能点击"停止"按钮中断回复

---

## 快速参考

| 操作 | 命令 |
|------|------|
| 启动后端 | `python run_api.py` |
| 启动前端 | `cd frontend && npm install && npm run dev` |
| 构建生产版本 | `cd frontend && npm run build` |
| 预览构建结果 | `cd frontend && npm run preview` |
| 查看API文档 | http://localhost:8000/docs |
| 访问前端应用 | http://localhost:3000 |
| 检查后端健康状态 | `curl http://localhost:8000/api/health` |

---

**更新日期**：2024-12-25  
**支持版本**：React 18 + FastAPI + Node.js 16+
