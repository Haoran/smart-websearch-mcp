# Smart Web Search MCP Server Docker Package

## 项目说明

这是一个基于 Docker 的智能网络搜索 MCP 服务器，使用 Anthropic Claude 进行 AI 驱动的搜索。

## 快速开始

```bash
# 构建并启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 环境变量说明

`.env` 文件包含以下配置：

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| ANTHROPIC_API_KEY | Anthropic API 密钥 | sk-ant-xxxxxxxxxxxxx |

## 测试服务

### 使用 Python 测试客户端

1. 安装依赖：
   ```bash
   pip install websockets
   ```

2. 运行测试：
   ```bash
   python test_mcp_client.py
   ```

### 手动测试

使用 WebSocket 客户端工具：
```bash
# 使用 wscat
npm install -g wscat
wscat -c ws://localhost:8765

# 发送初始化请求
{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}

# 列出工具
{"jsonrpc":"2.0","method":"tools/list","params":{},"id":2}

# 执行搜索
{"jsonrpc":"2.0","method":"tools/call","params":{"name":"smart_web_search","arguments":{"query":"什么是 Docker？"}},"id":3}
```

## 文件说明

```
mcp-server-docker/
├── docker-compose.yml      # Docker Compose 配置
├── Dockerfile             # Docker 镜像定义
├── requirements.txt       # Python 依赖
├── mcp_websearch_server.py # 服务器主程序
├── test_mcp_client.py     # 测试客户端
├── .env.example          # 环境变量模板
├── .env                  # 环境变量配置（需要创建）
└── README.md             # 本文档
```