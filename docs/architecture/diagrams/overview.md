# 产研数字军团OS — 系统全景架构图

## 产出文件

| 文件 | 说明 |
|------|------|
| `panoramic-architecture.excalidraw` | 可编辑的 Excalidraw 源文件（主交付物） |
| `generate_panoramic.py` | 生成器脚本，修改后可重新生成 |

## 架构概要

**三层两通道** 全景架构图 v3，包含以下关键决策：

### 第一层：终端用户层
- **一个产品，四个角色视图**（管理后台已合并）
- 经营管理者 / 复合型研发经理 / AI工程师 / AI Agent架构师
- 共享模块横条贯穿底部

### 通道1：HTTPS + REST API + SSE
- JWT Token 统一认证，Gateway 鉴权路由
- 四角色走同一入口，iam-svc 按 RBAC 控制

### 第二层：OS 服务端（3子层）
- **2a 技术网关**：gateway-svc（8085）
- **2b 业务服务**：4个微服务
  - pdm-svc（8080）— 核心业务
  - capability-svc（8081）— 产研能力定义（**workflow + agent 合并**）
  - iam-svc（8082）— 用户权限
  - inf-svc（8083）— 基础设施
- **2c 基础设施**：Nacos / RabbitMQ / PostgreSQL / Redis

### 通道2：WebSocket 长连接
- JSON-RPC 2.0 风格，WS-Token 认证（60min + 7天 refresh）

### 第三层：数字员工节点
- ACP 守护进程（7模块）+ 3种 Agent 实例（Hermes / Claude Code / HTTP Agent）

### 外部：LLM API
- inf-svc 统一代理，模型路由 + 降级切换

## v2→v3 关键变化

1. 管理后台合并到应用端（一个产品四角色视图）
2. workflow-svc + agent-svc → capability-svc（流程改必牵扯改人，避免分布式事务）
3. 服务数：7 → 5（MVP）

## 渲染说明

PNG 渲染因 macOS 沙箱限制未能自动完成（Playwright Chromium headless shell 的 Mach port 注册被拒绝）。

**替代方案**：
1. 在 Excalidraw 预览器中打开 `.excalidraw` → File → Export → PNG
2. 或访问 [excalidraw.com](https://excalidraw.com) → 打开文件 → 导出
