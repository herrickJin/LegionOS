# 产研数字军团 OS 微服务技术架构设计 v2

> 本文基于“全面微服务 + Spring Cloud”的方向重新整理，重点从工程落地角度说明：系统怎么拆、服务怎么通信、数据怎么放、数字员工和节点怎么运行、权限怎么传递，以及后续怎么演进。

## 1. 架构目标与设计约束

### 1.1 架构目标

产研数字军团 OS 的核心不是一个普通项目管理系统，而是一个“任务驱动的人机协作执行系统”。系统需要同时管理人类用户、数字员工、任务、项目、商机、资产、知识、流程、价值和基础执行环境。

架构目标如下：

| 目标             | 说明                                                              |
| -------------- | --------------------------------------------------------------- |
| 支撑 12 个业务域独立演进 | 经营决策、项目管理、项目实施、产研流程、基础设施、用户权限、数字员工、技术资产、知识体系、价值评估、自我进化、个人工作台    |
| 任务驱动           | 系统没有独立聊天入口，所有人机交互都围绕任务、任务上下文、任务产物和任务状态展开                        |
| 人和数字员工统一治理     | 数字员工作为特殊用户接入用户权限域，拥有 userId、角色、功能权限和可追溯身份                       |
| 流程规范和执行解耦      | 产研流程域只定义任务模板、任务 Spec、流程规则、工作台模板，不持有具体执行事实                       |
| 执行环境可替换        | AI 执行层可接入 Hermes、Claude Code、自研 Agent Runtime 或其他执行器，业务层不绑定具体实现 |
| 价值可追溯          | 任务、产物、数字员工调用、人工审核、成本和价值评估链路可追踪                                  |
| 微服务可演进         | 成熟形态按领域拆成服务，早期可先按核心链路收敛，但边界、接口和数据归属要按微服务设计                      |

### 1.2 关键约束

| 约束 | 设计结论 |
| --- | --- |
| 总体采用微服务架构 | 以 Spring Cloud 为主技术栈，服务按领域边界拆分 |
| 业务服务优先 Java | 核心业务服务使用 Spring Boot / Spring Cloud，便于事务、权限、工程治理和团队协作 |
| AI 执行层可用 Python | Agent Runtime、模型适配、工具调用、文件解析等适合使用 Python / FastAPI |
| 不做重型流程编排器 | P0 阶段不引入 Camunda/Temporal 等重型编排器，任务流程规则先进入任务上下文，由任务服务和执行服务按规则推进 |
| 不使用分布式事务 | 服务内本地事务；跨服务使用领域事件、Outbox、补偿任务保证最终一致 |
| 数据不强行一个库 | 权限、基础设施、数字员工、任务等核心域独立数据库或独立 schema；搜索、文件、向量能力按需引入 |
| 项目不是任务唯一来源 | 任务可以属于项目、商机、个人、知识、资产或系统，统一通过 Workspace 管理上下文资源边界 |

## 2. 总体技术架构

![产研数字军团 OS 系统划分与技术架构](./产研数字军团OS系统划分与技术架构图.svg)

总体上不要把所有东西都叫“客户端系统”。更清晰的划分是：

```text
产研数字军团 OS
├─ 用户可见系统
│  ├─ os-web
│  └─ admin-web
├─ 平台业务微服务
│  ├─ 12 个领域服务
│  └─ execution-service
├─ 平台内部 AI 执行系统
│  └─ ai-execution
└─ 外部执行节点代理
   └─ node-agent
```

这几个不是同一层级：

- `os-web`、`admin-web` 是用户能打开的系统。
- `ai-execution` 是平台内部执行系统，不是用户页面。
- `node-agent` 是安装在本地电脑、内网服务器或执行节点上的代理程序，不是 Web 系统。
- `任务工作台` 是 os-web 里的页面模块，不是独立系统。

总体上分为六层：

| 层级 | 组成 | 说明 |
| --- | --- | --- |
| 用户可见系统层 | os-web、admin-web | 业务用户和管理员直接使用的系统入口 |
| 接入与治理层 | API Gateway、Nacos、统一认证、限流、路由、审计 | 统一入口、认证前置、路由、服务发现、配置和可观测 |
| 平台业务微服务层 | 12 个领域服务 + execution-service | 承载业务事实、权限、任务、项目、流程、价值和执行记录 |
| AI 执行系统层 | ai-execution、ai-runtime、agent-adapter、model-adapter、tool-adapter | 承接执行请求，适配 Hermes、Claude Code、自研 Agent、模型和工具 |
| 外部执行节点层 | node-agent、Local Hermes、内网服务器、用户本地电脑 | 接入本地或外部执行环境，负责心跳、任务接收、权限拦截、日志回传 |
| 数据与资源层 | RDBMS、Redis、MQ、对象存储、搜索、Git、CI、模型服务 | 存储、事件、缓存、产物、知识检索和外部资源 |

### 2.1 系统上下文图

![产研数字军团 OS 系统上下文图](./产研数字军团OS系统上下文图.svg)

系统上下文图用于说明军团 OS 和外部对象的关系：

- 业务用户和管理员通过 os-web / admin-web 使用平台。
- 本地或内网执行环境通过 node-agent 接入平台。
- 模型服务通过 ai-execution 的 model-adapter 统一调用。
- Git、CI、IM、SSO、ONES/Jira 等外部系统通过 tool-adapter 或业务服务集成。
- 云端 Hermes 属于平台托管执行资源，本地 Hermes 属于外部执行节点。

### 2.2 核心服务组件图

![产研数字军团 OS 核心服务组件图](./产研数字军团OS核心服务组件图.svg)

核心组件图用于明确几个容易混淆的服务边界：

- task-service 持有任务事实、任务上下文、产物和人工确认。
- execution-service 持有一次执行请求和执行记录。
- infra-service 持有 Workspace、Node、Body、Instance 和资源策略。
- ai-execution 持有 Agent、模型、工具和文件解析适配能力。

### 2.3 执行链路时序图

![产研数字军团 OS 执行链路时序图](./产研数字军团OS执行链路时序图.svg)

执行链路图表达同一个任务执行接口如何支持两种路径：

- 云端 Hermes：`execution-service -> ai-execution -> Cloud Hermes`
- 本地 Hermes：`execution-service -> infra-service -> node-agent -> Local Hermes`

### 2.4 部署拓扑图

![产研数字军团 OS 部署拓扑图](./产研数字军团OS部署拓扑图.svg)

部署拓扑图区分四个运行区域：

- 平台云端 / 私有化部署区。
- 平台托管 AI 执行区。
- 外部执行节点区。
- 数据与中间件区。

## 3. 系统划分

### 3.1 最终交付系统

从产品交付和用户感知角度，建议分成 4 类系统。

| 系统 | 是否用户可见 | 类型 | 主要职责 |
| --- | --- | --- | --- |
| os-web | 是 | 业务前台 | 承载个人、商机、项目、任务、资产、知识、价值、自我进化等业务页面 |
| admin-web | 是 | 管理后台 | 承载用户权限、流程模板、数字员工原型、节点、模型、工具、系统参数配置 |
| ai-execution | 否 | 平台内部 AI 执行系统 | 承接 execution-service 的执行请求，适配 Agent、模型、工具、文件解析、执行策略 |
| node-agent | 否 | 执行节点代理 | 安装在本地电脑、内网服务器、云服务器或容器节点上，接入外部执行环境 |

这里要特别区分：

- `os-web` 是一个系统。
- `任务工作台` 是 os-web 的页面模块。
- `ai-execution` 是平台内部系统。
- `node-agent` 是代理程序，不是用户页面。

### 3.2 os-web 页面模块

os-web 是统一业务前台，不同角色看到的菜单和工作台不同。

| 页面模块  | 对应领域          | 说明                              |
| ----- | ------------- | ------------------------------- |
| 个人工作台 | 个人域           | 我的项目、我的任务、我的待办、我的资源             |
| 商机工作台 | 经营决策域         | 商机、情报、商机任务、推进状态                 |
| 项目工作台 | 项目管理域         | 项目详情、项目进度、项目资源、风险、变更            |
| 任务列表  | 项目实施域         | 项目任务、商机任务、个人任务、资产/知识任务          |
| 任务工作台 | 项目实施域 + 产研流程域 | 单任务执行现场：任务上下文、输入、AI 执行、产物、确认、反馈 |
| 资产工作台 | 技术资产域         | 工具、脚本、组件、模板、软件资产                |
| 知识工作台 | 知识体系域         | 文档、经验、复盘、知识检索                   |
| 价值看板  | 价值评估和结算域      | 任务价值、项目价值、AI 成本、ROI             |
| 进化反馈  | 自我进化域         | 问题反馈、优化建议、改进项                   |

因此，新建任务和查看任务详情不是两个系统之间跳转：

```text
os-web 项目工作台
  -> 新建任务
  -> os-web 任务工作台页面
```

用户仍然在同一个业务前台内，只是进入了任务执行页面。

### 3.3 admin-web 页面模块

admin-web 是配置和治理后台，不承载日常任务执行。

| 页面模块 | 对应领域 | 说明 |
| --- | --- | --- |
| 用户权限配置 | 用户权限域 | 用户、角色、功能权限、菜单权限 |
| 产研流程配置 | 产研流程域 | 任务模板、任务 Spec、流程规则、工作台模板 |
| 数字员工配置 | 数字员工域 | 原型、职责、技能、适用任务类型 |
| 基础设施配置 | 基础设施域 | 节点、Workspace、Body、实例、资源策略 |
| 模型工具配置 | 基础设施域 / 技术资产域 | 模型供应商、工具接入、工具权限 |
| 系统参数配置 | 平台治理 | 字典、开关、审计、运行参数 |

### 3.4 ai-execution 系统

ai-execution 是平台内部 AI 执行系统。它不是普通用户入口，也不直接承载项目、任务等业务事实。

| 模块 | 说明 |
| --- | --- |
| ai-runtime | Agent 执行入口，接收 execution-service 的执行请求 |
| agent-adapter | 适配 Hermes、Claude Code、自研 Agent |
| model-adapter | 适配内网模型、外部模型、本地模型，统一 Token 和成本统计 |
| tool-adapter | 适配 Git、CI、文件、IM、ONES/Jira 等工具 |
| file-parser | 解析 PDF、Word、Excel、Markdown、代码文件 |
| runtime-policy | 执行权限、工具权限、沙箱、资源边界校验 |

ai-execution 和业务服务的关系：

```text
task-service
  -> execution-service
  -> ai-execution
  -> Hermes / Claude Code / 自研 Agent
```

### 3.5 node-agent

node-agent 是执行节点代理，只在需要接入外部执行环境时使用。

| 场景 | 是否需要 node-agent |
| --- | --- |
| 使用军团 OS 云端 Hermes | 用户侧不需要 |
| 注册用户本地 Hermes | 需要 |
| 注册内网服务器 Hermes | 需要 |
| 服务器只是部署业务服务或数据库 | 不需要 |
| 服务器要作为执行节点运行数字员工 Body | 需要 |

node-agent 的职责：

- 注册 Node。
- 上报心跳和资源。
- 接收执行指令。
- 调用本地或服务器上的 Hermes。
- 拦截未授权目录、命令、Git 仓库和工具调用。
- 回传执行日志、状态和产物引用。

### 3.6 服务系统

服务分为三类，但它们都可以是独立微服务：

| 类型 | 说明 | 示例 |
| --- | --- | --- |
| 领域服务 | 持有某个业务域的核心数据和规则 | project-service、task-service、iam-service |
| 执行服务 | 负责把任务执行请求转成 AI Runtime 或节点调用 | execution-service、infra-service |
| 技术支撑服务 | 支撑网关、注册、配置、事件、缓存、监控 | gateway、nacos、rabbitmq、redis |

## 4. 微服务拆分

### 4.1 成熟期服务清单

| 服务 | 对应领域 | 主要职责 | 数据归属 | 建议技术 |
| --- | --- | --- | --- | --- |
| iam-service | 用户权限域 | 登录、Token、用户、角色、功能权限、菜单权限、数字员工用户身份 | iam_db | Spring Boot + Spring Security + JWT |
| personal-service | 个人工作台域 | 我的项目、我的任务、我的待办、个人视图聚合 | personal_db 或读模型 | Spring Boot |
| business-service | 经营决策域 | 商机、情报、商机任务、商机推进状态 | business_db | Spring Boot |
| project-service | 项目管理域 | 项目立项、资源申请、项目计划、风险、变更、项目资源关系 | project_db | Spring Boot |
| task-service | 项目实施域 | 任务、子任务、任务上下文、任务状态、产物、人工确认 | task_db | Spring Boot |
| process-service | 产研流程域 | 任务模板、任务 Spec、工作流规则、工作台模板 | process_db | Spring Boot |
| digital-worker-service | 数字员工域 | 数字员工原型、职责、技能、思维模式、适用任务类型 | worker_db | Spring Boot |
| infra-service | 基础设施域 | Workspace、Node、Body、实例、节点策略、部署策略 | infra_db | Spring Boot |
| execution-service | 执行调度域 | 执行请求、执行记录、执行状态、AI Runtime 适配入口 | execution_db | Spring Boot + OpenFeign/MQ |
| asset-service | 技术资产域 | 工具、脚本、组件、模板、软件资产、资产引用 | asset_db + search | Spring Boot |
| knowledge-service | 知识体系域 | 文档、经验、复盘、知识检索、知识引用 | knowledge_db + search/vector | Spring Boot |
| value-service | 价值评估和结算域 | 任务价值、项目价值、AI 成本、ROI、结算记录 | value_db | Spring Boot |
| evolution-service | 自我进化域 | 问题反馈、优化建议、改进项、处理闭环 | evolution_db | Spring Boot |

### 4.2 为什么需要 execution-service

`infra-service` 和 `execution-service` 容易混淆，建议这样划分：

| 服务 | 关注点 | 不负责什么 |
| --- | --- | --- |
| infra-service | 运行资源：节点、Workspace、Body、实例、部署、资源策略 | 不理解任务怎么执行，不直接解释任务 Spec |
| execution-service | 执行过程：执行请求、执行状态、执行日志、执行重试、调用 AI Runtime | 不管理节点资产，不管理 Body 生命周期 |
| ai-runtime | 具体执行器：调用模型、工具、文件解析、Agent 框架 | 不持有业务事实，不持有项目/任务主数据 |

一次数字员工执行时：

1. task-service 创建任务或子任务，并准备任务上下文。
2. task-service 根据任务类型从 process-service 获取任务执行规范。
3. task-service 向 execution-service 发起执行请求。
4. execution-service 查询 infra-service，找到可用 Workspace、Body、实例和节点。
5. execution-service 调用 ai-runtime 执行。
6. ai-runtime 调用模型、工具、文件解析或节点代理。
7. execution-service 回写执行记录和状态。
8. task-service 根据执行结果更新任务状态、产物和待确认事项。

### 4.3 数字员工服务和基础设施服务的边界

| 对象 | 所属服务 | 说明 |
| --- | --- | --- |
| DigitalWorkerPrototype | digital-worker-service | 数字员工原型：角色、职责、技能、思维方式、适合任务类型 |
| DigitalWorkerUser | iam-service | 数字员工身份：userId、userType、角色、功能权限 |
| DigitalWorkerBody | infra-service | 可部署的运行体定义：执行器类型、运行配置、工具配置、环境配置 |
| DigitalWorkerInstance | infra-service | 某次实际部署出来的实例：在哪个节点、什么状态、绑定哪个任务/项目 |
| ExecutionRecord | execution-service | 某次执行事实：输入、输出、日志、耗时、模型成本、状态 |

## 5. 技术选型

### 5.1 Java 业务服务

| 类别 | 选型 | 原因 |
| --- | --- | --- |
| 基础框架 | Spring Boot 3.2.x | Java 业务服务主框架，生态成熟，适合复杂业务和权限治理 |
| 微服务框架 | Spring Cloud 2023.x | 与 Spring Boot 3 兼容，便于服务发现、网关、Feign、配置治理 |
| 服务注册/配置 | Nacos 2.x | 注册中心和配置中心合一，国内团队使用经验较多 |
| 网关 | Spring Cloud Gateway | 统一入口、路由、认证、灰度、限流、审计 |
| 服务调用 | OpenFeign | Java 服务间同步调用，接口清晰，便于后期治理 |
| 消息队列 | RabbitMQ | 领域事件、异步执行、补偿任务，P0 到中期足够 |
| 安全 | Spring Security 6 + JWT | 统一认证、鉴权、Token 解析和权限上下文传递 |
| ORM | MyBatis Plus 或 Spring Data JDBC | 业务数据模型可控，SQL 可读性强 |
| 缓存 | Redis | 会话、权限缓存、任务状态缓存、节点心跳缓存 |
| 观测 | Actuator + Prometheus + Grafana | 指标采集、服务健康、基础可观测 |

### 5.2 Python AI 执行层

| 类别 | 选型 | 原因 |
| --- | --- | --- |
| 服务框架 | FastAPI | Python AI 服务常用，异步能力好，接口开发快 |
| 数据校验 | Pydantic | 适合 Agent 输入输出、工具参数、模型返回结构校验 |
| Agent 适配 | Adapter SPI | 让 Hermes、Claude Code、自研 Agent 都成为可替换实现 |
| 模型适配 | model-adapter | 统一 OpenAI、Claude、本地模型、私有模型的调用接口 |
| 工具适配 | tool-adapter | 统一 Git、CI、文件系统、ONES/Jira、IM 等工具 |
| 文件解析 | file-parser | 解析 PDF、Word、Excel、Markdown、代码文件，供任务上下文引用 |

### 5.3 关键 ADR

| ADR | 决策 |
| --- | --- |
| ADR-001 | 业务服务采用 Java / Spring Boot，AI 执行层采用 Python / FastAPI |
| ADR-002 | 采用 Spring Cloud Gateway 作为统一入口 |
| ADR-003 | 服务间同步调用使用 Feign，跨域状态变化优先使用事件 |
| ADR-004 | 不使用分布式事务，使用本地事务 + Outbox + 补偿 |
| ADR-005 | P0 不引入重型编排器，任务流程规则进入任务上下文，由 task-service/execution-service 推进 |
| ADR-006 | 数字员工身份归 iam-service，原型归 digital-worker-service，运行体和实例归 infra-service |
| ADR-007 | Hermes 不是架构本身，只是 ai-runtime 的一种 Agent Adapter 实现 |

## 6. 服务通信设计

### 6.1 同步调用

同步调用用于“当前请求必须立刻得到结果”的场景。

| 调用方 | 被调用方 | 场景 |
| --- | --- | --- |
| gateway | iam-service | 登录、Token 校验、用户权限解析 |
| project-service | iam-service | 检查用户是否具备项目管理功能权限 |
| project-service | process-service | 项目立项后选择任务模板 / 流程模板 |
| task-service | process-service | 创建任务时获取任务执行规范 |
| task-service | execution-service | 发起任务执行、查询执行状态 |
| execution-service | infra-service | 查询可用 Workspace、Body、实例和节点 |
| infra-service | digital-worker-service | 根据原型创建 Body 时读取原型定义 |
| infra-service | iam-service | 为数字员工 Body 绑定数字员工 userId |

同步调用使用 OpenFeign，接口定义放在 `os-common-api`，Feign 实现放在 `os-common-feign`。

### 6.2 异步事件

异步事件用于“状态变化通知、最终一致、价值计算、审计、反馈闭环”等场景。

| 事件 | 发布方 | 订阅方 |
| --- | --- | --- |
| UserRegisteredEvent | iam-service | personal-service、audit、digital-worker-service |
| DigitalWorkerUserRegisteredEvent | iam-service | digital-worker-service、infra-service |
| ProjectCreatedEvent | project-service | task-service、personal-service、value-service |
| ProjectResourceRequestedEvent | project-service | infra-service、digital-worker-service |
| TaskCreatedEvent | task-service | execution-service、personal-service、value-service |
| TaskExecutionStartedEvent | execution-service | task-service、value-service |
| TaskExecutionFinishedEvent | execution-service | task-service、value-service、evolution-service |
| ArtifactCreatedEvent | task-service | asset-service、knowledge-service、value-service |
| IssueFeedbackSubmittedEvent | task-service/process-service/infra-service | evolution-service |

事件统一进入 RabbitMQ：

| Exchange | 用途 |
| --- | --- |
| os.domain.events | 领域事件主交换机 |
| os.execution.events | 执行事件 |
| os.valuation.events | 价值评估事件 |
| os.audit.events | 审计事件 |

事件包结构建议：

```json
{
  "eventId": "evt_20260602_000001",
  "eventType": "TaskExecutionFinished",
  "sourceService": "execution-service",
  "traceId": "trace_xxx",
  "occurredAt": "2026-06-02T10:00:00+08:00",
  "version": "1.0",
  "payload": {
    "taskId": "task_001",
    "executionId": "exec_001",
    "status": "SUCCESS"
  }
}
```

### 6.3 调用选择原则

| 场景 | 方式 |
| --- | --- |
| 需要立即返回结果 | Feign |
| 状态变化通知多个服务 | MQ 事件 |
| 跨服务写操作 | 本地事务 + Outbox 事件 |
| 失败可重试 | MQ + 重试 + 补偿任务 |
| 强一致要求高 | 尽量收敛到同一个服务内完成 |
| AI 执行长任务 | execution-service 创建执行记录，异步调用 ai-runtime |

## 7. 数据架构

### 7.1 数据库划分原则

| 原则 | 说明 |
| --- | --- |
| 服务拥有自己的数据 | 其他服务不能直接写本服务表 |
| 可以共享数据库实例 | 早期可共享同一个 RDBMS 实例，但按库或 schema 隔离 |
| 读模型可以冗余 | personal-service、value-service 可以通过事件构建查询视图 |
| 跨服务不做分布式事务 | 使用 Outbox、事件、补偿任务 |
| 文件和产物不直接塞业务表 | 业务表只保存 fileId/artifactId/resourceRef，文件进入对象存储或 Git |

### 7.2 核心数据域

| 数据库 / Schema | 服务 | 核心表 |
| --- | --- | --- |
| iam_db | iam-service | iam_user、iam_role、iam_permission、iam_user_role、iam_role_permission、iam_menu |
| business_db | business-service | opportunity、opportunity_intelligence、opportunity_task_ref |
| project_db | project-service | project、project_member、project_resource_request、project_risk、project_change |
| task_db | task-service | task、sub_task、task_context、task_input、task_output、task_artifact、task_conversation |
| process_db | process-service | task_template、sub_task_template、task_spec、workflow_rule、workbench_template |
| worker_db | digital-worker-service | digital_worker_prototype、worker_skill、worker_task_type |
| infra_db | infra-service | workspace、workspace_resource、node、node_policy、digital_worker_body、digital_worker_instance |
| execution_db | execution-service | execution_request、execution_record、execution_log、execution_step |
| asset_db | asset-service | asset、asset_version、asset_ref、tool_definition |
| knowledge_db | knowledge-service | knowledge_doc、knowledge_chunk、knowledge_ref、experience_case |
| value_db | value-service | value_record、cost_record、settlement_record、roi_report |
| evolution_db | evolution-service | issue_feedback、improvement_suggestion、improvement_task |
| personal_db | personal-service | personal_todo、personal_view_cache、personal_task_index |

### 7.3 关键模型示例

#### 用户模型

```sql
CREATE TABLE iam_user (
  id BIGINT PRIMARY KEY,
  username VARCHAR(64) NOT NULL,
  display_name VARCHAR(128),
  user_type VARCHAR(32) NOT NULL, -- HUMAN / DIGITAL_WORKER
  org_id BIGINT,
  status VARCHAR(32) NOT NULL,
  created_at DATETIME NOT NULL
);

CREATE TABLE iam_user_role (
  user_id BIGINT NOT NULL,
  role_id BIGINT NOT NULL,
  PRIMARY KEY (user_id, role_id)
);
```

#### 任务模型

```sql
CREATE TABLE task (
  id BIGINT PRIMARY KEY,
  owner_type VARCHAR(32) NOT NULL, -- PROJECT / OPPORTUNITY / USER / ASSET / KNOWLEDGE / SYSTEM
  owner_id BIGINT NOT NULL,
  workspace_id BIGINT NOT NULL,
  task_type VARCHAR(64) NOT NULL,
  title VARCHAR(256) NOT NULL,
  status VARCHAR(32) NOT NULL,
  due_time DATETIME,
  created_by BIGINT NOT NULL,
  created_at DATETIME NOT NULL
);

CREATE TABLE task_context (
  id BIGINT PRIMARY KEY,
  task_id BIGINT NOT NULL,
  process_spec_id BIGINT,
  context_json JSON NOT NULL,
  version INT NOT NULL,
  updated_at DATETIME NOT NULL
);
```

#### 基础设施模型

```sql
CREATE TABLE infra_node (
  id BIGINT PRIMARY KEY,
  node_code VARCHAR(64) NOT NULL,
  node_type VARCHAR(32) NOT NULL, -- LOCAL_PC / SERVER / CONTAINER
  owner_user_id BIGINT,
  status VARCHAR(32) NOT NULL,
  heartbeat_at DATETIME,
  resource_json JSON,
  created_at DATETIME NOT NULL
);

CREATE TABLE digital_worker_body (
  id BIGINT PRIMARY KEY,
  prototype_id BIGINT NOT NULL,
  worker_user_id BIGINT NOT NULL,
  body_type VARCHAR(64) NOT NULL, -- HERMES / CLAUDE_CODE / CUSTOM
  config_json JSON NOT NULL,
  status VARCHAR(32) NOT NULL,
  created_at DATETIME NOT NULL
);

CREATE TABLE digital_worker_instance (
  id BIGINT PRIMARY KEY,
  body_id BIGINT NOT NULL,
  node_id BIGINT NOT NULL,
  workspace_id BIGINT NOT NULL,
  bind_owner_type VARCHAR(32),
  bind_owner_id BIGINT,
  status VARCHAR(32) NOT NULL,
  started_at DATETIME
);
```

## 8. 核心执行链路

### 8.1 项目申请数字员工并部署

1. project-service 创建项目资源申请，申请类型为数字员工。
2. project-service 调用 iam-service 注册数字员工用户，获得 `workerUserId`。
3. project-service 调用 digital-worker-service 选择数字员工原型。
4. project-service 调用 infra-service 创建 Workspace 资源绑定关系。
5. infra-service 根据 `prototypeId + workerUserId + workspaceId` 创建 DigitalWorkerBody。
6. infra-service 根据节点策略选择可部署节点。
7. infra-service 通过 node-agent 部署 DigitalWorkerInstance。
8. infra-service 返回实例信息给 project-service。
9. project-service 记录项目和数字员工资源关系。

这里的关键点：

- 数字员工先是一个用户，才能参与权限控制和审计。
- 原型决定“他是谁、会什么、适合干什么”。
- Body 决定“怎么运行、用什么执行器、带什么工具和环境配置”。
- Instance 决定“这一次部署在哪个节点、服务哪个 Workspace”。

### 8.2 创建任务并执行

1. 用户在 os-web 创建任务，或在 os-web 的任务工作台中拆分子任务。
2. task-service 保存任务主数据，确定 `ownerType/ownerId/workspaceId/taskType`。
3. task-service 调用 process-service 获取任务执行规范包。
4. 任务执行规范包写入 task_context 快照。
5. task-service 校验任务输入是否满足任务 Spec 的最低要求。
6. 如果缺少输入，例如前端开发任务缺少设计稿或组件规范，任务进入 `WAITING_INPUT`。
7. 输入完整后，task-service 调用 execution-service 发起执行。
8. execution-service 查询 infra-service，获取可用 Body/Instance/Node。
9. execution-service 调用 ai-runtime。
10. ai-runtime 执行 Agent、模型、工具和文件解析。
11. execution-service 回写执行记录。
12. task-service 更新任务状态、产物、待确认项。

任务执行规范包包括：

| 内容 | 来源 | 用途 |
| --- | --- | --- |
| 任务 Spec | process-service | 定义目标、输入、输出、验收标准、完成时间、执行人要求 |
| 工作流程规则 | process-service | 定义状态流转、人工接入点、异常处理、反馈规则 |
| 工作台模板 | process-service | 定义 os-web 任务工作台页面中应该展示哪些区域和操作 |

### 8.3 商机洞察任务

商机洞察不一定属于项目，因此不能强制挂项目。

设计方式：

- business-service 创建商机。
- task-service 创建任务，`ownerType=OPPORTUNITY`，`ownerId=opportunityId`。
- infra-service 为该商机创建或绑定 Workspace。
- digital-worker-service 选择适合“商机情报收集”的数字员工原型。
- execution-service 执行情报收集任务。
- 输出产物回到 business-service，作为商机情报或推进依据。

### 8.4 问题反馈与自我进化

1. 用户或数字员工在任务执行中发现流程、规范、工具、节点或权限问题。
2. task-service、process-service、infra-service 发布 `IssueFeedbackSubmittedEvent`。
3. evolution-service 记录问题反馈。
4. evolution-service 生成优化建议或改进任务。
5. 如果是流程模板问题，回流给 process-service。
6. 如果是节点或 Body 问题，回流给 infra-service。
7. 如果是数字员工能力问题，回流给 digital-worker-service。

## 9. 数字员工与节点架构

### 9.1 四层对象模型

| 层 | 对象 | 归属服务 | 说明 |
| --- | --- | --- | --- |
| 身份层 | User | iam-service | 数字员工也是用户，拥有 userId、角色、功能权限 |
| 原型层 | Prototype | digital-worker-service | 定义职责、技能、思维方式、适合任务 |
| 运行体层 | Body | infra-service | 定义具体执行器、工具、模型、环境 |
| 实例层 | Instance | infra-service | 某个 Body 在某个 Node 上的运行实例 |

### 9.2 Body 和原型的关系

Body 需要由原型创建。即使早期没有数字员工管理后台，也建议保留 `digital_worker_prototype` 表。

早期可以这样做：

1. 运维或架构师先在 infra-service 中定义可用 Body 配置。
2. 系统从 Body 配置中抽取角色、技能、执行器能力，反向同步到 digital-worker-service 的原型表。
3. 后续申请数字员工时，仍然通过原型选择，再创建新的 Body。

也就是说：

- 早期可以不做数字员工域的页面。
- 但数字员工原型数据仍然需要存在。
- 申请几个数字员工，就应创建几个 Body/Instance，而不是复用别的项目正在使用的 Body。

### 9.3 Node 注册

本地电脑注册到系统时，注册的是 Node，不是 Body。

Node 表示一个可承载执行的运行环境：

| Node 类型 | 示例 |
| --- | --- |
| LOCAL_PC | 用户本地电脑 |
| SERVER | 服务器 |
| CONTAINER_HOST | 容器宿主机 |
| K8S_NODE | Kubernetes 节点 |

Node 注册后不能被任意数字员工使用，需要通过节点策略控制：

- 哪些项目可以使用该节点。
- 哪些 Workspace 可以使用该节点。
- 哪些数字员工原型可以部署到该节点。
- 哪些工具可以在该节点使用。
- 本地路径白名单和敏感路径黑名单。
- 是否需要节点所有者审批。

### 9.4 执行权限拦截

如果数字员工被授权只能访问 A Git 仓库，但用户在任务对话里要求访问 B Git 仓库，系统应在工具调用层拦截。

拦截点：

| 拦截点 | 负责方 |
| --- | --- |
| 页面操作权限 | gateway + iam-service |
| 服务接口权限 | 各业务服务 |
| Workspace 资源权限 | task-service / project-service / infra-service |
| 工具调用权限 | ai-runtime 的 tool-adapter |
| 节点路径权限 | node-agent |
| 外部系统权限 | tool-adapter + 凭据管理 |

执行时，task-service 需要把 Workspace 授权资源写入任务上下文，execution-service 和 ai-runtime 只能使用上下文中声明的资源。

### 9.5 Hermes 接入的两种运行模式

Hermes 不应该被写死成系统架构的一部分。它应该被定义为一种 Agent Runtime 实现，可以通过不同运行模式接入产研数字军团 OS。

#### 模式一：本地 Hermes 接入

用户已经在自己的电脑或内网机器上运行 Hermes，希望把它注册到军团 OS，让平台可以把任务下发给它执行。

```text
用户本地电脑 / 内网服务器
  ├─ Hermes Runtime
  └─ node-agent
       ├─ 节点注册
       ├─ 心跳上报
       ├─ 接收执行指令
       ├─ 调用本地 Hermes
       ├─ 本地资源权限拦截
       └─ 执行日志回传

军团 OS
  ├─ infra-service
  ├─ execution-service
  └─ task-service
```

该模式下必须有 `node-agent`。

原因是军团 OS 后端不能直接操作用户电脑，也不能直接信任本地执行环境。`node-agent` 是本地 Hermes 和平台之间的受控连接器，负责注册、鉴权、心跳、执行指令、日志回传和本地权限拦截。

适用场景：

| 场景 | 说明 |
| --- | --- |
| 本地代码开发 | 数字员工需要访问用户本地代码目录 |
| 内网资源访问 | Hermes 需要访问公司内网 Git、测试环境、数据库或专用工具 |
| 私有执行环境 | 用户不希望代码和文件上传到云端执行 |
| 专用机器执行 | 某些任务需要固定机器、固定依赖或固定网络环境 |

本地模式的核心链路：

1. 用户安装 node-agent。
2. node-agent 向 infra-service 注册 Node。
3. 用户在军团 OS 中授权该 Node 可服务的项目、Workspace、任务类型和目录范围。
4. infra-service 在该 Node 上注册或绑定 Hermes Body。
5. task-service 发起任务执行。
6. execution-service 根据 Workspace 和节点策略选择该 Node。
7. execution-service 下发执行指令到 node-agent。
8. node-agent 调用本地 Hermes 执行。
9. node-agent 拦截越权文件、命令、Git 仓库或工具调用。
10. node-agent 回传执行日志和产物引用。

#### 模式二：军团 OS 云端 Hermes

军团 OS 平台自己提供云端 Hermes Runtime，用户只需要选择数字员工或执行能力，不需要安装本地代理。

```text
军团 OS 云端
  ├─ execution-service
  ├─ infra-service
  ├─ ai-runtime
  │    └─ Hermes Adapter
  └─ Hermes Runtime
```

该模式下，用户侧不需要 `node-agent`。

如果云端 Hermes 运行在平台自己管理的服务器或 Kubernetes 集群中，平台内部可以有 `node-agent` 或 runner 组件，但这是平台内部执行设施，不暴露给业务用户。

适用场景：

| 场景 | 说明 |
| --- | --- |
| 通用任务执行 | 需求分析、文档生成、测试用例生成、代码审查等 |
| 不依赖本地环境 | 输入材料都在平台 Workspace、Git、对象存储或知识库中 |
| 平台统一托管 | 由平台统一控制模型、工具、权限、日志和成本 |
| 弹性扩容 | 适合通过容器或云资源扩展执行能力 |

云端模式的核心链路：

1. 用户在任务中选择云端数字员工。
2. task-service 创建任务上下文。
3. execution-service 创建执行记录。
4. execution-service 调用 ai-runtime。
5. ai-runtime 通过 Hermes Adapter 调用云端 Hermes。
6. Hermes 通过平台提供的工具适配器访问 Workspace 授权资源。
7. execution-service 接收执行结果并回写 task-service。

### 9.6 两种模式的统一抽象

为了同时支持本地 Hermes 和云端 Hermes，建议抽象出统一的执行目标 `ExecutionTarget`。

| 字段 | 说明 |
| --- | --- |
| targetType | CLOUD_RUNTIME / EXTERNAL_NODE |
| runtimeType | HERMES / CLAUDE_CODE / CUSTOM_AGENT |
| nodeId | 本地或外部节点模式下必填 |
| bodyId | 绑定的数字员工 Body |
| instanceId | 实际运行实例 |
| workspaceId | 本次执行可访问的资源边界 |
| policyId | 执行策略，包括命令、目录、工具、网络权限 |

统一执行接口：

```text
execution-service.executeTask(taskId, executionTarget, executionContext)
```

不同模式只影响执行路由：

| 模式 | execution-service 路由 |
| --- | --- |
| 云端 Hermes | execution-service -> ai-runtime -> Hermes Adapter |
| 本地 Hermes | execution-service -> infra-service/node-channel -> node-agent -> local Hermes |

业务服务不关心 Hermes 在哪里运行，只关心：

- 这个数字员工是谁。
- 这个任务要执行什么。
- 这个 Workspace 允许访问哪些资源。
- 执行结果、日志、产物和状态是什么。

## 10. 安全架构

### 10.1 认证

用户登录流程：

1. os-web 调用 gateway。
2. gateway 路由到 iam-service。
3. iam-service 校验账号密码或 SSO。
4. iam-service 签发 JWT。
5. 前端后续请求携带 JWT。
6. gateway 校验 JWT，解析用户信息。
7. gateway 将用户上下文透传给下游服务。

JWT 建议包含：

```json
{
  "sub": "10001",
  "userType": "HUMAN",
  "orgId": "org_001",
  "roles": ["PROJECT_MANAGER"],
  "permissions": ["project:create", "task:execute"],
  "iat": 1780000000,
  "exp": 1780003600
}
```

### 10.2 鉴权

鉴权分两层：

| 层级 | 说明 |
| --- | --- |
| 功能权限 | 用户是否能访问某个菜单、按钮、接口能力，由 iam-service 管 |
| 资源权限 | 用户是否能访问某个项目、任务、Workspace、Git 仓库，由对应业务服务管 |

用户权限域不管理具体项目数据权限。

例如：

- 研发工程师是否有“项目实施”功能权限，由 iam-service 判断。
- 研发工程师是否能访问项目 A，由 project-service 判断。
- 数字员工是否能访问 A Git，由 Workspace 资源策略和 tool-adapter 判断。

### 10.3 数字员工认证

数字员工执行时可以使用两种方式：

| 方式 | 说明 |
| --- | --- |
| Agent JWT | iam-service 为数字员工 userId 签发短期 Token |
| Execution Credential | execution-service 为一次执行生成短期凭证，只能访问指定 Workspace 资源 |

建议组合使用：

- 数字员工身份使用 Agent JWT。
- 工具和资源访问使用 Execution Credential。
- 凭证有效期短，绑定 executionId、taskId、workspaceId。

## 11. 部署架构

### 11.1 开发环境

开发环境建议使用 Docker Compose：

| 组件 | 用途 |
| --- | --- |
| MySQL/PostgreSQL | 业务数据库 |
| Redis | 缓存、会话、心跳 |
| RabbitMQ | 领域事件、执行事件 |
| Nacos | 注册中心、配置中心 |
| MinIO | 文件、产物、附件 |
| OpenSearch/Elasticsearch | 搜索、知识检索 |
| Prometheus/Grafana | 指标监控 |

P0 可以先不上 OpenSearch、MinIO、完整 ELK：

- 文件和产物可以先放 Git 或本地对象存储。
- 日志先用应用日志 + Prometheus/Grafana。
- 知识检索早期可以先普通全文检索，后续再上向量库。

### 11.2 生产环境

生产环境建议：

| 层 | 部署方式 |
| --- | --- |
| gateway | Kubernetes / Docker，至少 2 副本 |
| Java 微服务 | Kubernetes / Docker，按服务独立部署 |
| Python AI Runtime | 独立部署，可按执行压力水平扩容 |
| node-agent | 安装在本地电脑、服务器或容器节点 |
| MQ/Redis/DB | 独立中间件集群或托管服务 |
| 监控 | Prometheus + Grafana + 日志平台 |

## 12. 工程结构

建议工程结构：

```text
legion-os/
  pom.xml
  os-common/
    os-common-core/
    os-common-security/
    os-common-api/
    os-common-feign/
    os-common-event/
  os-gateway/
  os-services/
    iam-service/
    personal-service/
    business-service/
    project-service/
    task-service/
    process-service/
    digital-worker-service/
    infra-service/
    execution-service/
    asset-service/
    knowledge-service/
    value-service/
    evolution-service/
  ai-runtime/
    app/
      agent_adapter/
      model_adapter/
      tool_adapter/
      file_parser/
      runtime_policy/
  node-agent/
  deploy/
    docker-compose/
    k8s/
  docs/
```

说明：

- `os-common-api` 放 Facade 接口、DTO、事件定义。
- `os-common-feign` 放 Feign Client 实现。
- 服务内部实现自己的 Controller、Application Service、Domain Service、Repository。
- 业务服务依赖 `os-common-api`，需要远程调用时依赖 `os-common-feign`。
- 切换微服务时，不需要改业务调用方的接口定义，只需要把本地 Facade 实现替换为 Feign 实现。

## 13. P0 到成熟期演进

虽然目标是微服务架构，但落地可以分阶段。

### 13.1 P0

P0 建议先做能支撑任务驱动闭环的最小微服务集：

| 服务 | 说明 |
| --- | --- |
| gateway | 统一入口 |
| iam-service | 登录、用户、角色、权限、数字员工用户 |
| project-service | 项目、项目资源申请 |
| task-service | 任务、任务上下文、任务产物 |
| process-service | 任务模板、任务 Spec、流程规则、工作台模板 |
| infra-service | Workspace、Node、Body、Instance |
| execution-service | 执行请求、执行记录、调用 AI Runtime |
| ai-runtime | Agent、模型、工具适配 |

其余服务可以先保留接口和数据边界，按需要逐步实现。

### 13.2 增长期

增长期补齐：

- business-service：商机洞察任务。
- digital-worker-service：数字员工原型管理。
- asset-service：工具、脚本、组件资产。
- knowledge-service：知识文档、经验沉淀、检索。
- value-service：价值和成本评估。
- evolution-service：问题反馈和优化闭环。
- personal-service：个人工作台聚合。

### 13.3 成熟期

成熟期重点：

- 每个域独立服务、独立数据库或 schema。
- MQ 增加 DLQ、重试、补偿任务。
- 引入 Sentinel / SkyWalking / OpenTelemetry。
- 节点支持容器化部署和弹性调度。
- 数字员工支持多执行器、多模型、多工具策略。
- 价值评估形成自动化指标体系。

## 14. 主要风险与控制

| 风险 | 表现 | 控制方式 |
| --- | --- | --- |
| 服务拆太细，早期开发慢 | 接口多、联调复杂 | 按成熟架构设计，按 P0 最小微服务集实现 |
| 任务上下文失控 | 输入、文件、产物、权限散落 | task_context 统一快照，文件用 resourceRef，Workspace 管资源边界 |
| 数字员工越权 | Agent 访问未授权仓库或工具 | Workspace 资源策略 + tool-adapter 拦截 + node-agent 路径白名单 |
| AI Runtime 绑定某个实现 | 后续 Hermes/Claude Code 替换困难 | Agent Adapter SPI，业务层只调用 execution-service |
| 跨服务一致性问题 | 项目申请资源成功但部署失败 | Outbox + 状态机 + 补偿任务 |
| 节点安全风险 | 本地电脑被任意任务调用 | 节点注册审批、部署策略、路径白名单、执行凭证短期化 |
| 价值评估不可信 | 无法追踪任务贡献和 AI 成本 | execution_record、artifact、value_record 关联 taskId/executionId |

## 15. 架构文档完整性对照

对照常见架构文档框架，当前文档已经覆盖总体架构、服务拆分、技术选型、数据架构、执行链路、安全和部署，并在本版补充了系统上下文图、核心服务组件图、执行链路时序图、部署拓扑图、核心接口契约、横切关注点、ADR 和风险控制。

| 标准维度 | 当前覆盖情况 | 后续深化方向 |
| --- | --- | --- |
| 系统上下文 | 已补系统上下文图 | 后续可继续细化外部系统接口协议和认证方式 |
| 容器/服务视图 | 已补系统划分与技术架构图 | 后续可补每个服务的入站 API、出站依赖、事件发布/订阅 |
| 组件视图 | 已补核心服务组件图 | 后续可继续补 iam-service、process-service、digital-worker-service 的组件图 |
| 运行时视图 | 已补任务执行时序图 | 后续可补项目申请数字员工、节点注册、权限拦截时序图 |
| 部署视图 | 已补部署拓扑图 | 后续可补 Kubernetes Deployment、Service、Ingress 级别部署图 |
| 数据视图 | 已补数据生命周期、任务上下文版本、产物存储、文件引用规则 | 后续可补更详细 ER 图 |
| 接口契约 | 已补核心 API 契约 | 后续可输出 OpenAPI / AsyncAPI |
| 横切关注点 | 已补熔断、限流、幂等、重试、补偿、审计、配置、灰度 | 后续可按服务细化策略 |
| ADR | 已补关键 ADR 明细 | 后续可拆成独立 ADR 文档 |
| 风险 | 已补风险等级、影响范围、控制措施、验证方式 | 后续可进入项目风险台账 |

本版已补充图：

| 图 | 目的 |
| --- | --- |
| 系统划分与技术架构图 | 统一说明 os-web、admin-web、业务服务、ai-execution、node-agent 的层级关系 |
| 系统上下文图 | 说明军团 OS 和用户、执行节点、模型服务、研发工具、企业系统的关系 |
| 核心服务组件图 | 说明 task-service、execution-service、infra-service、ai-execution 的内部职责 |
| 执行链路时序图 | 说明云端 Hermes 和本地 Hermes 的两条执行路径 |
| 部署拓扑图 | 区分平台云端、AI 执行区、外部执行节点、数据中间件 |

## 16. 数据生命周期设计

### 16.1 任务数据生命周期

任务是整个平台的核心执行单元，任务数据生命周期如下：

```text
创建任务
  -> 选择任务类型 / 流程模板
  -> 生成任务上下文快照
  -> 补齐输入资源
  -> 发起执行
  -> 记录执行过程
  -> 生成产物
  -> 人工确认 / 反馈
  -> 归档 / 价值评估 / 知识沉淀
```

| 阶段 | 主服务 | 核心数据 | 说明 |
| --- | --- | --- | --- |
| 创建任务 | task-service | task、sub_task | 保存任务主数据、ownerType、ownerId、workspaceId |
| 选择规范 | process-service | task_template、task_spec、workflow_rule | 提供任务执行规范包 |
| 上下文快照 | task-service | task_context | 保存本次任务使用的 Spec、流程规则、输入资源引用 |
| 执行请求 | execution-service | execution_request、execution_record | 记录本次执行的输入、目标、状态和 traceId |
| 资源解析 | infra-service | workspace_resource、node、body、instance | 解析可访问资源、可用 Body、执行节点 |
| AI 执行 | ai-execution | execution_step、runtime_log | 调用 Agent、模型、工具和文件解析 |
| 产物生成 | task-service | task_artifact、task_output | 保存产物引用，不直接保存大文件 |
| 价值评估 | value-service | value_record、cost_record | 统计任务价值、模型成本、人工成本、ROI |
| 知识沉淀 | knowledge-service | knowledge_doc、experience_case | 对可复用产物和经验进行沉淀 |

### 16.2 任务上下文版本

任务上下文必须支持版本化，因为任务执行过程中输入、流程规则、资源授权都可能发生变化。

| 字段 | 说明 |
| --- | --- |
| contextId | 任务上下文 ID |
| taskId | 任务 ID |
| version | 上下文版本号 |
| processSpecSnapshot | 任务 Spec 快照 |
| workflowRuleSnapshot | 工作流规则快照 |
| workbenchTemplateSnapshot | 工作台模板快照 |
| inputRefs | 输入资源引用 |
| workspaceResourceRefs | Workspace 授权资源引用 |
| createdBy | 创建人或系统 |
| createdAt | 创建时间 |

规则：

- 每次发起执行前生成新的上下文快照。
- execution-service 只使用本次 executionId 绑定的 contextVersion。
- 流程模板后续修改不影响已执行任务。
- 如果执行中补充输入，需要生成新 contextVersion，再重新执行或继续执行。

### 16.3 产物存储和文件引用

业务表不直接保存大文件，只保存资源引用。

| 文件类型 | 建议存储 | 业务表保存 |
| --- | --- | --- |
| 用户上传附件 | 对象存储 / 本地文件服务 | fileId、fileName、sha256、storageUri |
| 代码产物 | Git 仓库 | repoId、branch、commitId、path |
| 文档产物 | 对象存储 + 知识库索引 | fileId、knowledgeDocId |
| 日志 | 日志系统 / 对象存储 | logId、traceId、executionId |
| 测试报告 | 对象存储 / CI 系统 | reportId、ciBuildId、storageUri |

文件引用统一模型：

```text
ResourceRef
├─ resourceType: FILE / GIT_REPO / GIT_COMMIT / DOC / TOOL / ENV / URL
├─ resourceId
├─ uri
├─ version
├─ checksum
├─ ownerType
├─ ownerId
└─ workspaceId
```

这样后续查询任务输入、执行产物、知识沉淀、价值评估时，都可以通过 `workspaceId + resourceRef` 找到实际资源。

### 16.4 Workspace 数据生命周期

Workspace 归 infra-service 管理，但业务对象持有 workspaceId 引用。

```text
创建项目 / 商机 / 个人任务
  -> 创建或绑定 Workspace
  -> 绑定资源
  -> 绑定可用数字员工 Body / Instance
  -> 绑定可用节点和工具
  -> 任务执行时引用 Workspace
  -> 结束后归档或释放资源
```

| 生命周期阶段 | 处理方式 |
| --- | --- |
| 创建 | project-service/business-service/task-service 请求 infra-service 创建 Workspace |
| 授权 | infra-service 维护 workspace_resource、workspace_policy |
| 使用 | task-service 在 task_context 中引用 workspaceId 和资源引用 |
| 执行 | execution-service 根据 workspaceId 查询可用执行目标 |
| 变更 | 资源授权变更生成新策略版本 |
| 归档 | 项目结束或任务归档后，Workspace 保留引用和审计记录 |

## 17. 核心 API 契约

这里只定义系统运转必须具备的核心接口，不展开完整字段。

### 17.1 iam-service

| 接口 | 使用者 | 说明 |
| --- | --- | --- |
| `POST /api/iam/login` | os-web、admin-web | 用户登录，返回 JWT |
| `POST /internal/iam/users/human` | admin-web、业务服务 | 注册人类用户 |
| `POST /internal/iam/users/digital-worker` | project-service、infra-service | 注册数字员工用户 |
| `GET /internal/iam/users/{userId}` | 各业务服务 | 查询用户基础信息 |
| `GET /internal/iam/users/{userId}/roles` | gateway、业务服务 | 查询用户角色 |
| `GET /internal/iam/users/{userId}/permissions` | gateway、业务服务 | 查询功能权限 |
| `POST /internal/iam/permissions/check` | gateway、业务服务 | 校验功能权限 |

### 17.2 process-service

| 接口 | 使用者 | 说明 |
| --- | --- | --- |
| `GET /internal/process/task-templates` | project-service、task-service、os-web | 查询可用任务模板 |
| `GET /internal/process/task-templates/{templateId}` | task-service | 查询任务模板详情 |
| `GET /internal/process/execution-package` | task-service | 获取任务执行规范包：任务 Spec、工作流规则、工作台模板 |
| `POST /internal/process/feedback` | task-service、evolution-service | 提交流程或规范问题反馈 |

### 17.3 task-service

| 接口 | 使用者 | 说明 |
| --- | --- | --- |
| `POST /api/tasks` | os-web | 创建任务 |
| `POST /api/tasks/{taskId}/sub-tasks` | os-web | 拆分子任务 |
| `GET /api/tasks/{taskId}` | os-web | 查询任务详情 |
| `GET /api/tasks/{taskId}/context` | os-web、execution-service | 查询任务上下文 |
| `POST /api/tasks/{taskId}/inputs` | os-web | 补充任务输入 |
| `POST /api/tasks/{taskId}/execute` | os-web | 发起任务执行 |
| `POST /internal/tasks/{taskId}/execution-result` | execution-service | 回写执行结果 |
| `POST /api/tasks/{taskId}/confirm` | os-web | 人工确认任务产物 |

### 17.4 infra-service

| 接口 | 使用者 | 说明 |
| --- | --- | --- |
| `POST /internal/infra/workspaces` | project-service、business-service、task-service | 创建 Workspace |
| `GET /internal/infra/workspaces/{workspaceId}` | task-service、execution-service | 查询 Workspace |
| `POST /internal/infra/workspaces/{workspaceId}/resources` | os-web、project-service | 绑定 Workspace 资源 |
| `GET /internal/infra/execution-targets` | execution-service | 查询可用执行目标 |
| `POST /internal/infra/bodies` | project-service、infra-service | 创建数字员工 Body |
| `POST /internal/infra/instances/deploy` | infra-service、node-agent | 部署数字员工实例 |
| `POST /internal/infra/nodes/register` | node-agent | 注册节点 |
| `POST /internal/infra/nodes/{nodeId}/heartbeat` | node-agent | 节点心跳 |

### 17.5 execution-service

| 接口 | 使用者 | 说明 |
| --- | --- | --- |
| `POST /internal/executions` | task-service | 创建执行请求 |
| `GET /internal/executions/{executionId}` | task-service、os-web | 查询执行状态 |
| `POST /internal/executions/{executionId}/cancel` | task-service、os-web | 取消执行 |
| `POST /internal/executions/{executionId}/callback` | ai-execution、node-agent | 回调执行状态 |
| `GET /internal/executions/{executionId}/logs` | os-web、task-service | 查询执行日志 |

### 17.6 ai-execution

| 接口 | 使用者 | 说明 |
| --- | --- | --- |
| `POST /internal/ai-runtime/execute` | execution-service | 发起云端 AI 执行 |
| `POST /internal/ai-runtime/tools/call` | agent-adapter | 调用工具适配器 |
| `POST /internal/ai-runtime/files/parse` | task-service、execution-service | 解析文件 |
| `GET /internal/ai-runtime/runtimes` | execution-service | 查询可用 Runtime |

### 17.7 事件契约

| 事件 | 发布方 | 订阅方 |
| --- | --- | --- |
| `TaskCreatedEvent` | task-service | personal-service、value-service |
| `TaskExecutionStartedEvent` | execution-service | task-service、value-service |
| `TaskExecutionFinishedEvent` | execution-service | task-service、value-service、evolution-service |
| `WorkspaceResourceChangedEvent` | infra-service | task-service、execution-service |
| `DigitalWorkerBodyDeployedEvent` | infra-service | project-service、digital-worker-service |
| `IssueFeedbackSubmittedEvent` | task-service、process-service、infra-service | evolution-service |

## 18. 横切关注点设计

### 18.1 熔断与限流

| 对象 | 策略 |
| --- | --- |
| gateway | 按用户、租户、接口、IP 限流 |
| Feign 调用 | 超时、重试、熔断、降级返回 |
| ai-execution | 按模型供应商、Runtime、任务类型限流 |
| node-agent | 按节点并发、CPU、内存、磁盘资源限流 |
| 外部工具 | 按工具类型和凭据限流，避免触发外部系统限制 |

P0 可以先使用网关限流 + Feign 超时，增长期再引入 Sentinel 或 Resilience4j。

### 18.2 幂等

必须幂等的接口：

| 接口 | 幂等键 |
| --- | --- |
| 创建任务 | `clientRequestId` |
| 发起执行 | `taskId + contextVersion + requestId` |
| 部署 Body | `bodyId + nodeId + workspaceId` |
| 执行回调 | `executionId + stepId + statusVersion` |
| 事件消费 | `eventId` |

幂等处理原则：

- 写接口必须支持重复请求。
- 事件消费必须记录消费日志。
- 执行回调必须按版本推进，不允许旧状态覆盖新状态。

### 18.3 重试与补偿

| 场景 | 处理 |
| --- | --- |
| Feign 查询失败 | 短重试，失败后降级 |
| MQ 消费失败 | 重试队列，超过次数进入补偿任务 |
| AI 执行失败 | execution-service 记录失败原因，可按策略重试 |
| node-agent 断连 | infra-service 标记节点不可用，execution-service 转人工或重新调度 |
| Body 部署失败 | infra-service 释放中间状态，记录补偿任务 |

不建议使用分布式事务。跨服务状态变化使用：

```text
本地事务
  -> Outbox 事件
  -> MQ 投递
  -> 消费方本地事务
  -> 失败补偿
```

### 18.4 审计

需要审计的行为：

- 用户登录、登出、Token 刷新。
- 用户权限变更。
- 创建项目、任务、Workspace。
- 数字员工注册、Body 创建、实例部署。
- 任务执行、取消、重试、人工确认。
- 工具调用、Git 访问、文件读取、命令执行。
- 权限拦截和越权尝试。

审计字段：

| 字段 | 说明 |
| --- | --- |
| auditId | 审计 ID |
| userId | 操作主体，人或数字员工 |
| userType | HUMAN / DIGITAL_WORKER |
| action | 操作 |
| targetType | 目标类型 |
| targetId | 目标 ID |
| workspaceId | 资源上下文 |
| traceId | 链路 ID |
| result | SUCCESS / FAIL / DENIED |
| occurredAt | 发生时间 |

### 18.5 配置与灰度

| 配置类型 | 所属 |
| --- | --- |
| 路由配置 | gateway / Nacos |
| 服务参数 | Nacos |
| 模型配置 | admin-web + infra-service / ai-execution |
| 工具配置 | asset-service / infra-service |
| 流程模板 | process-service |
| 数字员工原型 | digital-worker-service |
| 节点策略 | infra-service |

灰度策略：

- 服务版本灰度：按用户、组织、项目、任务类型。
- 模型灰度：按任务类型、数字员工原型、Workspace。
- 流程模板灰度：按模板版本、项目类型。
- Agent Runtime 灰度：同一数字员工原型可绑定不同 Runtime 实现。

## 19. ADR 明细

### ADR-001：业务服务采用 Java，AI 执行层采用 Python

| 项 | 内容 |
| --- | --- |
| 背景 | 业务服务需要稳定事务、权限、审计、工程治理；AI 执行层需要快速适配模型、Agent、工具和文件解析 |
| 选项 | 全 Java、全 Python、Java + Python |
| 决策 | 业务服务 Java / Spring Boot，AI 执行层 Python / FastAPI |
| 后果 | 服务边界清晰，但需要处理 Java 与 Python 的接口契约和运行监控 |

### ADR-002：采用 Spring Cloud 微服务体系

| 项 | 内容 |
| --- | --- |
| 背景 | 12 个领域长期会独立演进，需要服务注册、配置、网关、服务调用和治理能力 |
| 选项 | 单体、模块化单体、Spring Cloud 微服务 |
| 决策 | 架构按微服务设计，P0 可控制服务数量，但边界按微服务落地 |
| 后果 | 前期复杂度提升，但长期边界清晰，便于拆分和团队协作 |

### ADR-003：任务工作台属于 os-web，不独立成系统

| 项 | 内容 |
| --- | --- |
| 背景 | 用户新建任务后需要自然进入任务详情和执行现场，不应该感知跨系统跳转 |
| 选项 | 独立 task-workbench、os-web 内页面模块、微前端子应用 |
| 决策 | 当前作为 os-web 内页面模块，后续复杂后可拆成微前端子应用 |
| 后果 | 用户体验统一，前期开发简单，同时保留后续独立演进空间 |

### ADR-004：infra-service 和 execution-service 暂不合并

| 项 | 内容 |
| --- | --- |
| 背景 | infra-service 管运行资源，execution-service 管一次执行事实，二者职责不同但调用紧密 |
| 选项 | 合并为 runtime-service、拆成 infra + execution |
| 决策 | 暂不合并，保持 infra-service 和 execution-service 独立 |
| 后果 | 服务数量增加，但 Workspace、Node、Body、Instance 和执行记录边界更清晰 |

### ADR-005：不引入重型编排器

| 项 | 内容 |
| --- | --- |
| 背景 | 当前任务流程主要是任务模板、任务 Spec、工作流规则和人工确认点，不需要复杂 BPMN |
| 选项 | Camunda、Temporal、轻量规则推进 |
| 决策 | P0 不引入重型编排器，由 task-service + execution-service 按流程规则推进 |
| 后果 | 前期简单可控，但复杂长流程出现后需要重新评估 |

### ADR-006：Hermes 是 Agent Runtime 实现，不是架构核心

| 项 | 内容 |
| --- | --- |
| 背景 | 后续可能使用 Hermes、Claude Code、自研 Agent 或其他执行器 |
| 选项 | 绑定 Hermes、抽象 Agent Adapter |
| 决策 | Hermes 作为 agent-adapter 的一种实现 |
| 后果 | 架构可替换，但需要定义统一执行输入、输出、日志和权限拦截协议 |

## 20. 风险控制

| 风险 | 等级 | 影响范围 | 控制措施 | 验证方式 |
| --- | --- | --- | --- | --- |
| 服务拆分过细导致联调复杂 | 高 | 全平台交付效率 | P0 控制服务数量，优先打通 iam、project、task、process、infra、execution | 核心链路端到端联调 |
| Workspace 定义不清导致权限混乱 | 高 | 任务执行、数字员工、资源访问 | Workspace 归 infra-service，业务域只保存 workspaceId 引用 | 设计权限拦截测试用例 |
| 数字员工越权访问资源 | 高 | 安全、代码、文件、内网系统 | Workspace 白名单、tool-adapter 拦截、node-agent 路径拦截、审计记录 | 模拟访问未授权 Git/目录 |
| AI 执行结果不可追踪 | 高 | 任务验收、价值评估、问题复盘 | execution_record 记录输入、输出、日志、traceId、模型成本 | 从任务追溯到执行日志和产物 |
| 本地 Hermes 接入不稳定 | 中 | 本地执行任务 | node-agent 心跳、断线重连、失败重试、转云端或转人工 | 断网、重启、超时压测 |
| 跨服务数据不一致 | 中 | 项目、任务、执行状态 | Outbox、事件幂等、补偿任务、状态机推进 | 重复消息、乱序消息测试 |
| 流程模板变更影响历史任务 | 中 | 任务执行正确性 | task_context 保存模板快照和版本 | 修改模板后验证历史任务上下文 |
| 模型成本失控 | 中 | 成本、价值评估 | model-adapter 做 Token 统计、预算限制、任务类型限额 | 按任务统计成本报表 |
| 节点执行环境不可信 | 中 | 本地安全、命令执行 | 节点审批、路径白名单、命令白名单、凭据短期化 | 权限攻击演练 |
| 管理后台配置错误 | 中 | 流程、权限、节点 | 配置审批、版本化、回滚、变更审计 | 配置回滚演练 |

## 21. 结论

推荐采用“Spring Cloud 微服务业务层 + Python AI 执行层 + node-agent 执行节点网络”的架构。

业务侧按 12 个领域拆分，确保项目、任务、流程、权限、数字员工、基础设施、价值和演进都有清晰边界。执行侧通过 execution-service 和 ai-runtime 解耦具体 Agent 实现，使 Hermes、Claude Code 或自研执行器都只是可替换适配器。节点侧由 infra-service 管理 Node、Body、Instance 和 Workspace 资源边界，保证数字员工执行可部署、可审计、可控制。

这套架构的关键不是一开始把所有服务都做满，而是先把边界、接口、数据归属和执行链路设计正确。P0 做最小微服务集，后续按复杂度和业务优先级逐步拆出完整 12 域服务。
