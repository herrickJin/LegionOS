# 产研数字军团OS PRD

## 6. 架构设计（全面微服务 + Spring Cloud）

---

### 6.1 架构目标与约束

**目标：**
- **建立统一的人机协同执行层：人类员工和数字员工共享同一套身份、任务、评估体系**
- 支撑12个业务域的独立演进与协同运行
- 保证价值积分计算的准确性与可追溯性
- 满足多组织层级的数据隔离与权限控制

**约束：**
- **演进式微服务：** MVP阶段4+1个聚合服务，成长期拆分为8个，成熟期完整12个（详见6.16）
- **Spring Cloud 技术栈：** 统一注册发现、配置中心、网关
- **事件驱动优先：** 域间通信以异步事件为主，同步OpenFeign为辅
- **混合数据策略：** 核心聚合域共享数据库实例但Schema隔离，独立域各自独立数据库
- **最终一致：** 价值评估、统计报表等场景允许秒级延迟
- **无分布式事务：** core_db内本地事务，跨服务用事件+补偿，不引入Seata

> **MVP阶段简化：** 工作流只支持线性执行（无分支/并行），数字员工采用远程LLM API调用（无容器化），事件总线无死信队列（失败人工处理），无Sentinel/SkyWalking

---

### 6.2 服务划分（成熟期完整架构）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              产研数字军团OS                                   │
│                           （Spring Cloud 微服务架构）                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Spring Cloud Gateway                            │   │
│  │                      （统一入口 / 路由 / 限流 / 鉴权）                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Nacos（注册中心 + 配置中心）                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Sentinel（熔断降级 + 流量控制）                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      SkyWalking（链路追踪 + APM）                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐   │
│  │          │          │          │          │          │          │   │
│  │ 经营决策  │ 项目管理  │ 项目实施  │ 产研流程  │ 数字员工  │ 技术资产  │   │
│  │ 服务     │ 服务     │ 服务     │ 服务     │ 服务     │ 服务     │   │
│  │ opp-svc  │ prj-svc  │ tsk-svc  │ wf-svc   │ agt-svc  │ ast-svc  │   │
│  │          │          │          │          │          │          │   │
│  └──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘   │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐              │
│  │          │          │          │          │          │              │
│  │ 知识经验  │ 基础设施  │ 用户权限  │ 自我进化  │ 价值评估  │              │
│  │ 服务     │ 服务     │ 服务     │ 服务     │ 服务     │              │
│  │ knw-svc  │ inf-svc  │ iam-svc  │ evo-svc  │ val-svc  │              │
│  │          │          │          │          │          │              │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘              │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Portal Service（BFF / 个人域）                    │   │
│  │                      聚合各域数据，提供统一前端接口                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      基础设施层（中间件）                              │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐              │   │
│  │  │  RabbitMQ │ │  Redis   │ │  MySQL   │ │  MongoDB │              │   │
│  │  │ (事件总线) │ │ (缓存)   │ │ (关系数据)│ │ (文档数据)│              │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘              │   │
│  │  ┌──────────┐ ┌──────────┐                                         │   │
│  │  │Elasticsearch│ │  MinIO   │                                         │   │
│  │  │ (搜索引擎)  │ │ (对象存储)│                                         │   │
│  │  └──────────┘ └──────────┘                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

> **MVP阶段服务聚合详见6.16演进式拆分策略**

---

### 6.3 服务清单（成熟期）

| 服务名 | 服务ID | 对应域 | 端口范围 | 数据库 | 说明 |
|--------|--------|--------|---------|--------|------|
| opp-svc | opportunity-service | 经营决策域 | 8100 | MongoDB | 商机、MRD管理 |
| prj-svc | project-service | 项目管理域 | 8200 | **core_db(MySQL)** | 项目、里程碑、迭代 |
| tsk-svc | task-service | 项目实施域 | 8300 | **core_db(MySQL)** | 任务、交付物、验收 |
| wf-svc | workflow-service | 产研流程域 | 8400 | **core_db(MySQL)** | 工作流规范、节点编排、判定规则、执行工作台 |
| agt-svc | agent-service | 数字员工域 | 8500 | MySQL+Redis | 原型、实例、灵魂配置 |
| ast-svc | asset-service | 技术资产域 | 8600 | MySQL+ES | 资产、复用记录 |
| knw-svc | knowledge-service | 知识经验域 | 8700 | MongoDB+ES | 知识条目、FAQ |
| inf-svc | infra-service | 基础设施域 | 8800 | MySQL+Redis | 节点、Body实例、项目上下文 |
| iam-svc | iam-service | 用户权限域 | 8900 | **iam_db(MySQL)** | 用户、角色、组织、权限 |
| evo-svc | evolution-service | 自我进化域 | 9000 | MongoDB | 改进需求、解决方案 |
| val-svc | valuation-service | 价值评估域 | 9100 | MySQL | 积分、规则、报告、兑换 |
| portal-svc | portal-service | 个人域(BFF) | 9200 | 无 | 数据聚合、视图组装 |

> **core_db：** prj-svc + tsk-svc + wf-svc 共享核心库，支撑高频聚合查询与事务

---

### 6.4 Spring Cloud 技术栈

| 组件 | 选型 | 用途 |
|------|------|------|
| **Spring Boot** | 3.2.x | 基础框架 |
| **Spring Cloud** | 2023.0.x | 微服务全家桶 |
| **Spring Cloud Gateway** | 4.x | API网关（路由/限流/鉴权） |
| **Nacos** | 2.3.x | 注册中心 + 配置中心 |
| **OpenFeign** | 4.x | 服务间同步调用 |
| **Sentinel** | 1.8.x | 熔断降级 + 流量控制 |
| **SkyWalking** | 9.x | 链路追踪 + APM |
| **Spring Data** | 3.x | 数据访问（JPA/Mongo/Redis） |
| **Spring Security** | 6.x | 认证授权（OAuth2 Resource Server） |

---

### 6.5 通信架构

#### 6.5.1 同步通信（OpenFeign）

```java
// 经营决策服务 → 项目管理服务：查询项目详情
@FeignClient(name = "project-service", fallbackFactory = ProjectClientFallback.class)
public interface ProjectClient {
    @GetMapping("/api/v1/projects/{projectId}")
    ProjectDTO getProject(@PathVariable String projectId);
}

// 带熔断降级
@Component
@Slf4j
public class ProjectClientFallback implements ProjectClient {
    @Override
    public ProjectDTO getProject(String projectId) {
        log.warn("project-service 降级，projectId={}", projectId);
        return ProjectDTO.empty();
    }
}
```

**适用场景：**
| 源服务 | 目标服务 | 场景 | 理由 |
|--------|---------|------|------|
| portal-svc | 任意服务 | 数据聚合查询 | BFF层需要实时数据组装，带超时降级 |
| tsk-svc | agt-svc | 任务分配确认 | 需即时确认执行者是否可用 |
| agt-svc | inf-svc | 实例化请求 | 需等待资源分配结果 |
| 任意服务 | iam-svc | 用户信息查询 | 缓存未命中时回源，非权限校验 |

#### 6.5.2 异步通信（RabbitMQ）

**事件发布示例：**
```java
@Component
public class DomainEventPublisher {
    @Autowired
    private RabbitTemplate rabbitTemplate;
    
    public void publishMRDApproved(MRDApprovedEvent event) {
        rabbitTemplate.convertAndSend(
            "os.domain.events",
            "opp.mrd.approved",
            event,
            msg -> {
                msg.getMessageProperties().setHeader("source", "opportunity-service");
                msg.getMessageProperties().setHeader("version", "1.0");
                msg.getMessageProperties().setDeliveryMode(MessageDeliveryMode.PERSISTENT);
                return msg;
            }
        );
    }
}
```

**事件消费示例（带重试）：**
```java
@Component
@RabbitListener(queues = "project.mrd.approved")
public class MRDApprovedConsumer {
    @RabbitHandler
    public void handle(MRDApprovedEvent event) {
        try {
            projectService.createFromMRD(event);
        } catch (Exception e) {
            log.error("MRD消费失败, mrdId={}", event.getMrdId());
            throw e; // 触发重试或进入死信队列
        }
    }
}
```

**Exchange 设计：**

| Exchange | 事件 | 消费者 |
|----------|------|--------|
| os.domain.events | opp.mrd.approved | prj-svc, portal-svc |
| os.domain.events | prj.project.created | portal-svc, val-svc |
| os.domain.events | wf.task.assigned | tsk-svc, agt-svc |
| os.domain.events | tsk.task.completed | wf-svc, val-svc |
| os.domain.events | agt.instance.ready | tsk-svc, portal-svc |
| os.domain.events | ast.asset.reused | val-svc |
| os.domain.events | knw.knowledge.cited | val-svc |
| os.valuation.events | val.point.calculated | portal-svc |
| os.notification.events | notify.risk.alert | portal-svc |

**事件格式：**
```json
{
  "eventId": "evt-uuid-v7",
  "eventType": "opp.mrd.approved",
  "sourceService": "opportunity-service",
  "payload": { "mrdId": "MRD-2024-001", ... },
  "timestamp": "2024-01-15T10:00:01Z",
  "version": "1.0"
}
```

#### 6.5.3 通信决策矩阵

| 源服务 | 目标服务 | 场景 | 方式 | 组件 |
|--------|---------|------|------|------|
| opp-svc | prj-svc | MRD移交 | 异步事件 | RabbitMQ |
| wf-svc | tsk-svc | 工作流规范发布 | 异步事件 | RabbitMQ |
| tsk-svc | wf-svc | 执行评价回流 | 异步事件 | RabbitMQ |
| wf-svc | tsk-svc | 任务分配 | **同步RPC** | OpenFeign |
| tsk-svc | agt-svc | 任务分配确认 | 同步RPC | OpenFeign |
| agt-svc | inf-svc | 实例化请求 | 同步RPC | OpenFeign |
| inf-svc | agt-svc | 状态变更通知 | 异步事件 | RabbitMQ |
| ast-svc | val-svc | 资产复用 | 异步事件 | RabbitMQ |
| knw-svc | val-svc | 知识引用 | 异步事件 | RabbitMQ |
| evo-svc | val-svc | 改进解决 | 异步事件 | RabbitMQ |
| 任意 | portal-svc | 数据聚合 | 同步RPC | OpenFeign + 超时降级 |
| 任意 | iam-svc | 用户信息查询 | 同步RPC | OpenFeign + 本地缓存 |

---

### 6.6 数据架构

#### 6.6.1 数据库分配（混合策略）

| 服务 | 数据库 | 选型理由 |
|------|--------|---------|
| opp-svc | MongoDB | MRD结构灵活，文档型存储 |
| **prj-svc** | **core_db(MySQL)** | 项目关系复杂，与任务/流程高频联动 |
| **tsk-svc** | **core_db(MySQL)** | 任务状态流转需ACID，与项目/流程强事务 |
| **wf-svc** | **core_db(MySQL)** | 工作流规范与项目关联，聚合查询多 |
| agt-svc | MySQL + Redis | 元数据关系型，运行时状态缓存 |
| ast-svc | MySQL + ES | 资产元数据+全文检索 |
| knw-svc | MongoDB + ES | 知识文档+全文检索 |
| inf-svc | MySQL + Redis | 节点管理+上下文缓存 |
| **iam-svc** | **iam_db(MySQL)** | RBAC标准化模型，用户数据权威源 |
| evo-svc | MongoDB | 改进需求非结构化 |
| val-svc | MySQL | 积分计算需精确事务 |
| portal-svc | 无 | 只读聚合，不存储 |

#### 6.6.2 核心库（core_db）设计

core_db采用**Schema隔离**，prj-svc/tsk-svc/wf-svc各拥有独立Schema，通过数据库用户权限限制跨Schema访问。

**核心表结构：**

```sql
-- 项目管理域（prj_schema）
CREATE TABLE prj_project (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(256) NOT NULL,
    status ENUM('已创建','进行中','已暂停','已交付','已归档'),
    manager_id VARCHAR(64) NOT NULL,     -- 关联iam_db.sys_user.id
    org_id VARCHAR(64) NOT NULL,
    mrd_id VARCHAR(64),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_org_id(org_id),
    INDEX idx_status(status)
);

-- 项目实施域（tsk_schema）
CREATE TABLE tsk_task (
    id VARCHAR(64) PRIMARY KEY,
    project_id VARCHAR(64) NOT NULL,
    name VARCHAR(256) NOT NULL,
    status ENUM('待分配','待开始','进行中','待审查','已完成','已验收','待返工','已阻塞','已取消'),
    assignee_id VARCHAR(64),             -- 关联iam_db.sys_user.id
    assignee_type ENUM('HUMAN','AGENT'), -- 区分人和数字员工
    workflow_id VARCHAR(64),
    spec_id VARCHAR(64),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_project_id(project_id),
    INDEX idx_assignee_id(assignee_id),
    INDEX idx_status(status)
);

-- 产研流程域（wf_schema）
CREATE TABLE wf_task_spec (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(256) NOT NULL,
    status ENUM('草稿','已发布','已停用'),
    skill_requirement JSON,
    created_by VARCHAR(64),
    org_id VARCHAR(64),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE wf_workflow (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(256),
    status ENUM('草稿','已发布','已停用'),
    spec_id VARCHAR(64) NOT NULL,        -- 必须关联工作流规范
    definition JSON,
    FOREIGN KEY (spec_id) REFERENCES wf_task_spec(id)
);
```

> 完整Schema定义见数据库迁移脚本（db/migration/V1__init_schema.sql）

#### 6.6.3 用户权限库（iam_db）设计

```sql
-- 用户表（人 + 数字员工）
CREATE TABLE sys_user (
    id VARCHAR(64) PRIMARY KEY,
    username VARCHAR(64) NOT NULL UNIQUE,
    password_hash VARCHAR(256),          -- 数字员工可为空（API Key认证）
    user_type ENUM('HUMAN','AGENT') NOT NULL DEFAULT 'HUMAN',
    real_name VARCHAR(64),
    org_id VARCHAR(64) NOT NULL,
    status ENUM('启用','禁用','删除') DEFAULT '启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_org_id(org_id),
    INDEX idx_user_type(user_type)
);

-- 角色表
CREATE TABLE sys_role (
    id VARCHAR(64) PRIMARY KEY,
    role_code VARCHAR(64) NOT NULL UNIQUE,
    role_name VARCHAR(64) NOT NULL
);

-- 角色权限关联表（对应第4章角色矩阵）
CREATE TABLE sys_role_permission (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    role_code VARCHAR(64) NOT NULL,
    domain VARCHAR(64) NOT NULL,
    perm_type VARCHAR(64) NOT NULL,
    UNIQUE KEY uk_role_domain_perm (role_code, domain, perm_type)
);

-- 数字员工扩展表
CREATE TABLE sys_agent_user (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL UNIQUE,
    prototype_id VARCHAR(64),
    instance_id VARCHAR(64),
    skills JSON,
    max_concurrent_tasks INT DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES sys_user(id)
);
```

> 完整角色矩阵初始化数据见 db/migration/V2__init_roles.sql

#### 6.6.4 用户数据同步机制

```
iam-svc（权威源）→ RabbitMQ(os.iam.events) → 各服务Redis本地缓存

事件类型：iam.user.created / iam.user.updated / iam.user.disabled / iam.role.changed
缓存策略：TTL=1小时，收到事件主动刷新，未命中时OpenFeign调iam-svc
```

**事件格式：**
```java
public class UserChangedEvent {
    private String eventType;
    private String userId;
    private String userType;      // HUMAN / AGENT
    private String orgId;
    private List<String> roles;
}
```

#### 6.6.5 数据隔离策略

```
MySQL实例：
├─ core_db（prj_schema + tsk_schema + wf_schema）
├─ iam_db（用户权限）
├─ agt_db / ast_db / val_db / inf_db（独立库）
└─ evo_db / opp_db（MongoDB）
```

**隔离规则：**
- core_db内：Schema隔离，各服务独立数据库用户，禁止跨Schema访问
- 独立库：物理隔离，通过事件/RPC交互
- 所有业务表必须含 `org_id` 字段，应用层过滤数据范围
- 跨组织查询需显式申请权限（iam-svc校验）

#### 6.6.6 关键数据流

```
MRD创建流：
  用户 → Gateway → opp-svc → opp_db(MongoDB)
  
MRD移交流：
  opp-svc → RabbitMQ → prj-svc → core_db(MySQL)
  
任务分配流（核心库内事务）：
  tsk-svc → core_db: 查询任务
         → OpenFeign(wf-svc查询规则)
         → OpenFeign(agt-svc实例化)
         → OpenFeign(inf-svc分配节点)
         → core_db: 更新任务状态（本地事务）
  
积分计算流：
  各服务 → RabbitMQ → val-svc → val_db(MySQL)
  
数据聚合流：
  前端 → Gateway → portal-svc → 并行OpenFeign查询各服务 → 聚合响应
  
用户数据查询流：
  各服务 → Redis本地缓存 → 未命中 → OpenFeign(iam-svc) → 写入缓存
```

---

#### 6.7.1 数字员工执行模式（MVP简化）

**MVP阶段：** 数字员工执行采用"远程API调用"模式，不自研运行时容器。

**MVP阶段inf-svc职责范围：**
- **仅管理项目上下文**（外部系统接口配置、GitLab/Jira连接信息）
- **不管理Body实例**（无k8s集成、无容器调度、无心跳监控）
- agt-svc直接调用外部LLM API，无需inf-svc介入资源分配

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────────────────┐
│   agt-svc   │────→│  灵魂配置   │────→│  外部LLM API（OpenAI/Claude） │
│  (任务路由)  │     │(Prompt模板) │     │  按任务类型选择模型和参数      │
└─────────────┘     └─────────────┘     └─────────────────────────────┘
       │
       ▼
┌─────────────┐
│  知识库引用  │
│(RAG检索相关 │
│  知识条目)   │
└─────────────┘
```

**执行流程：**
1. agt-svc接收任务，查询灵魂配置（Prompt模板 + 模型参数）
2. 从知识经验域检索相关知识条目，组装上下文
3. 调用外部LLM API执行任务
4. 返回执行结果，记录到任务执行日志

**MVP约束：**
- 不支持Body容器化部署（无k8s集成）
- 不支持数字员工实例的独立运行时环境
- 不支持实例心跳和故障恢复（由agt-svc统一调度）
- 资源消耗（token用量）由agt-svc记录并推送价值评估域

**后续演进：**
- Phase 2：inf-svc保留项目上下文管理，新增数字员工资源消耗记录（token用量）
- Phase 3：引入Body容器化部署（k8s/Docker），inf-svc扩展为资源调度+Body生命周期管理
- Phase 4：支持实例独立运行时、心跳监控、故障自动恢复

---

#### 6.7.2 数字员工运行时（完整版，Phase 3+）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            数字员工运行时（Spring Cloud）                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────┐    ┌─────────────────────────────────────┐│
│  │      agt-svc（逻辑管理）      │    │      inf-svc（资源调度）             ││
│  │                             │    │                                     ││
│  │  ┌─────────────────────┐   │    │  ┌─────────────────────────────┐   ││
│  │  │   AgentPrototype    │   │    │  │      K8s Operator           │   ││
│  │  │   原型管理（JPA）    │   │    │  │  （Body生命周期管理）          │   ││
│  │  │   - 思维模式         │   │    │  │                             │   ││
│  │  │   - 知识库配置       │   │    │  │  ┌─────────────────────┐   │   ││
│  │  │   - 技能配置         │   │    │  │  │   Body Pod          │   │   ││
│  │  │   - 行为准则         │   │    │  │  │   ┌─────────────┐   │   │   ││
│  │  └─────────────────────┘   │    │  │  │   │ Soul Runtime │   │   │   ││
│  │  ┌─────────────────────┐   │    │  │  │   │ (AI推理引擎)  │   │   │   ││
│  │  │   AgentInstance     │   │    │  │  │   │ - 思维模式    │   │   │   ││
│  │  │   实例管理（JPA）    │   │    │  │  │   │ - 知识库检索  │   │   │   ││
│  │  │   - 状态跟踪         │   │    │  │  │   │ - 技能调用    │   │   │   ││
│  │  │   - 运行时上下文     │   │    │  │  │   └─────────────┘   │   │   ││
│  │  │   - user_id关联      │   │    │  │  │   ┌─────────────┐   │   │   ││
│  │  └─────────────────────┘   │    │  │  │   │ Body Runtime │   │   │   ││
│  │  ┌─────────────────────┐   │    │  │  │   │ (执行环境)    │   │   │   ││
│  │  │   SoulConfig        │   │    │  │  │   │ - 环境检测    │   │   │   ││
│  │  │   灵魂配置（MongoDB）│   │    │  │  │   │ - 部署脚本    │   │   │   ││
│  │  │   - Prompt模板       │   │    │  │  │   │ - 任务上下文  │   │   │   ││
│  │  │   - 知识库向量       │   │    │  │  │   └─────────────┘   │   │   ││
│  │  └─────────────────────┘   │    │  │  └─────────────────────┘   │   ││
│  │                             │    │  │                             │   ││
│  │  状态机：设计中→测试中→已发布   │    │  │  实例状态：创建中→待分配→执行中  │   ││
│  │          已下线→已废弃         │    │  │            →闲置→已回收        │   ││
│  │                             │    │  │                             │   ││
│  └─────────────────────────────┘    │  └─────────────────────────────┘   ││
│                                                                             │
│  灵魂知识库：Redis（私有命名空间，按实例隔离）                                  │
│  组织知识库：Elasticsearch（知识经验域共享）                                   │
│  项目Memory：Redis（按项目隔离，TTL=项目周期）                                │
│                                                                             │
│  数字员工身份链路：                                                           │
│  agt-svc创建实例 → 调iam-svc创建sys_user（role=AI_ENGINEER）                │
│  → sys_agent_user记录prototype/instance关联 → 实例获得user_id可登录调API      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**关键设计：**
- 灵魂与Body分离：agt-svc管理逻辑，inf-svc管理物理运行
- 数字员工身份：实例化时agt-svc调iam-svc创建用户，获得user_id，实现"数字员工也是用户"
- 实例故障恢复：
  - inf-svc检测到Body故障 → 尝试重启（计数器由inf-svc维护）
  - 第1/2次失败：通知agt-svc更新状态为"故障中"
  - 第3次失败：通知agt-svc更新状态为"已销毁"
  - agt-svc检查进行中任务 → 有则发送重新分配事件到tsk-svc
- 闲置回收：agt-svc定时任务扫描，超阈值调用inf-svc回收API
- 知识库分层：Redis(私有) → ES(组织级)，执行时先查私有再查组织级
- 网络分区处理：inf-svc定期心跳到agt-svc，30秒未收到标记"失联"，需人工确认

---

### 6.8 安全架构

#### 6.8.1 认证流程（OAuth2 + JWT）

```
用户 → Gateway → iam-svc（验证）→ 返回JWT → Gateway缓存公钥 → 后续请求验签
```

**JWT结构：**
```json
{
  "sub": "user-001",
  "name": "张三",
  "userType": "HUMAN",
  "orgId": "org-001",
  "orgPath": "org-001/org-002",
  "roles": ["COMPOSITE_MANAGER"],
  "permissions": ["opp:read", "prj:write"],
  "iat": 1705312800,
  "exp": 1705399200
}
```

#### 6.8.2 权限校验（Gateway做完整校验，服务层做数据范围过滤）

```java
// Gateway层：路由级权限 + 透传用户信息
@Component
public class AuthGatewayFilter implements GlobalFilter {
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        String path = exchange.getRequest().getPath().value();
        String token = extractToken(exchange);
        JWTClaims claims = jwtUtil.parse(token);
        
        // 校验路由权限
        if (!claims.hasPermission(path)) {
            return forbidden(exchange);
        }
        
        // 透传用户信息到下游服务
        exchange.getRequest().mutate()
            .header("X-User-Id", claims.getSub())
            .header("X-User-Type", claims.getUserType())
            .header("X-Org-Id", claims.getOrgId())
            .header("X-Org-Path", claims.getOrgPath())
            .header("X-Roles", String.join(",", claims.getRoles()))
            .build();
        
        return chain.filter(exchange);
    }
}

// 服务层：数据范围校验（示例）
@Service
public class ProjectService {
    public List<Project> listProjects(String userId, String orgId, String orgPath) {
        // Gateway已校验权限，服务层只过滤数据范围
        List<String> orgIds = extractSubOrgIds(orgPath);
        return projectRepository.findByOrgIdIn(orgIds);
    }
}
```

#### 6.8.3 数字员工特殊权限

```java
// 数字员工功能权限（iam-svc管理）
public class AgentIAMConfig {
    private String userId;
    private String agentId;
    private List<String> apiPermissions;   // 能调用的API
    private List<String> dataScopes;       // 数据可见范围
}

// 数字员工业务能力（agt-svc灵魂配置）
public class AgentSoulConfig {
    private String agentId;
    private List<String> skills;
    private List<String> taskTypes;        // 可执行的任务类型
    private int maxConcurrentTasks;
    private String knowledgeBaseVersion;
}
```

**两域解耦：**
- iam-svc决定"能不能登录、能不能调API"（功能权限）
- agt-svc决定"能执行什么任务、执行到什么程度"（业务能力）

**数字员工认证方式：**
```java
// 数字员工使用API Key认证
@PostMapping("/api/v1/agents/authenticate")
public TokenResponse authenticateAgent(@RequestHeader("X-Agent-Key") String agentKey) {
    AgentInstance instance = agentService.validateKey(agentKey);
    UserDTO user = iamClient.getUser(instance.getUserId());
    String jwt = jwtUtil.generateAgentToken(user, instance);
    return new TokenResponse(jwt);
}
```

---

### 6.9 非功能性需求

**MVP阶段（Phase 0-1）适用指标：**

| 指标 | 目标 | 实现方式 |
|------|------|---------|
| 系统可用性 | 99.5% | Nacos健康检查 + 单副本（开发环境） |
| API响应时间(P99) | <1s | Redis缓存 + 数据库索引 |
| 服务间调用(P99) | <200ms | OpenFeign连接池 |
| 事件消费延迟 | <10秒 | RabbitMQ消费者组 |
| 积分计算延迟 | <5分钟 | 异步事件 + 批量计算 |
| 分布式事务 | 最终一致 | 本地事务 + 事件补偿 |
| 监控告警 | 15分钟发现 | Actuator端点 + 日志告警 |
| 消息可靠性 | 不丢失 | 持久化消息 + 生产者确认 + 消费者ack |

**成熟期（Phase 4+）完整指标：**

| 指标 | 目标 | Spring Cloud 实现 |
|------|------|------------------|
| 系统可用性 | 99.9% | Nacos健康检查 + k8s自动重启 + 多副本 |
| API响应时间(P99) | <500ms | Sentinel限流 + Redis缓存 + 数据库索引 |
| 服务间调用(P99) | <100ms | OpenFeign连接池 + 本地缓存 |
| 事件消费延迟 | <5秒 | RabbitMQ消费者组 + 批量消费(100条/批) |
| 积分计算延迟 | <1分钟 | 异步事件 + 批量计算(500条/批) |
| 分布式事务 | 最终一致 | ~~Seata AT模式~~ → 本地事务 + 事件补偿 |
| 链路追踪 | 全链路 | SkyWalking自动埋点 |
| 熔断降级 | 秒级恢复 | Sentinel规则：错误率>50%熔断10秒 |
| API版本控制 | 平滑演进 | URL版本（/api/v1/, /api/v2/），事件版本兼容 |
| 监控告警 | 5分钟发现 | Prometheus + Grafana + 业务指标 |
| 消息可靠性 | 不丢失 | 持久化消息 + 生产者确认 + 消费者ack + 死信队列 |

---

### 6.10 部署架构

**开发环境（Docker Compose）：**

```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  nacos:
    image: nacos/nacos-server:v2.3.0
    ports: ["8848:8848"]
  rabbitmq:
    image: rabbitmq:3.12-management
    ports: ["5672:5672", "15672:15672"]
  mysql:
    image: mysql:8.0
    ports: ["3306:3306"]
    environment:
      MYSQL_ROOT_PASSWORD: root
  mongodb:
    image: mongo:7.0
    ports: ["27017:27017"]
  redis:
    image: redis:7.0
    ports: ["6379:6379"]
  elasticsearch:
    image: elasticsearch:8.11.0
    ports: ["9200:9200"]
    environment:
      - discovery.type=single-node
```

**生产环境（Kubernetes）：**

```yaml
# opp-svc-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: opportunity-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: opportunity-service
  template:
    spec:
      containers:
      - name: opp-svc
        image: legionos/opportunity-service:1.0.0
        ports:
        - containerPort: 8100
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

**资源规划：**

| 服务 | 副本数 | CPU请求 | 内存请求 | 数据库 |
|------|--------|---------|---------|--------|
| gateway | 2 | 500m | 512Mi | 无 |
| opp-svc | 3 | 500m | 512Mi | MongoDB |
| prj-svc | 5 | 1000m | 1Gi | core_db(MySQL) |
| tsk-svc | 5 | 1000m | 1Gi | core_db(MySQL) |
| wf-svc | 3 | 500m | 512Mi | core_db(MySQL) |
| agt-svc | 3 | 2000m | 4Gi | MySQL+Redis |
| ast-svc | 2 | 500m | 512Mi | MySQL+ES |
| knw-svc | 2 | 500m | 512Mi | MongoDB+ES |
| inf-svc | 3 | 1000m | 2Gi | MySQL+Redis |
| iam-svc | 3 | 500m | 512Mi | iam_db(MySQL) |
| evo-svc | 2 | 500m | 512Mi | MongoDB |
| val-svc | 3 | 1000m | 1Gi | MySQL |
| portal-svc | 2 | 500m | 512Mi | 无 |

---

### 6.11 与现有系统集成

| 现有系统 | 集成方式 | 涉及服务 | 技术实现 |
|---------|---------|---------|---------|
| GitLab | Webhook + REST API | inf-svc, tsk-svc | GitLab4J API + WebhookController |
| Jira/ONES | REST API | prj-svc, tsk-svc | OpenFeign客户端 |
| 企业微信/钉钉 | Webhook | portal-svc | RestTemplate推送消息 |
| 云厂商(AWS/阿里云) | SDK | inf-svc | 云厂商Java SDK |
| 内部SSO | OAuth2/SAML | iam-svc, gateway | Spring Security OAuth2 |
| AI推理服务 | HTTP API | agt-svc | WebClient异步调用 |

---

### 6.12 架构验证（对照第5章场景）

| 场景 | 架构支撑点 | 验证结果 |
|------|-----------|---------|
| SC-01 MRD移交 | opp-svc发布RabbitMQ事件 → prj-svc消费 → core_db | ✅ 异步解耦，最终一致 |
| SC-12 任务分配 | tsk-svc OpenFeign调wf-svc查规则（core_db内本地查询） | ✅ 同步查询，延迟<100ms |
| SC-12 实例化 | agt-svc OpenFeign调inf-svc分配资源 | ✅ 同步等待，失败熔断 |
| SC-04 资产复用 | ast-svc发布事件 → val-svc幂等消费 | ✅ 异步计算，批量处理 |
| SC-03 评价回流 | tsk-svc(core_db)发布事件 → wf-svc(core_db)消费优化 | ✅ 同库事件，低延迟 |
| SC-05 积分兑换 | val-svc本地事务（积分冻结→扣减/解冻） | ✅ 单服务事务，强一致 |
| SC-06 改进跟踪 | evo-svc MongoDB存储 + 优先级队列 | ✅ 非结构化，灵活查询 |
| SC-07 跨组织权限 | Gateway JWT校验 + 服务层org_id过滤 | ✅ 双层防护，数据隔离 |

---

### 6.13 项目结构规范

```
legion-os/
├── pom.xml                          # 父POM
├── legion-os-gateway/               # Gateway
├── legion-os-common/                # 公共模块（事件/DTO/异常/工具）
├── legion-os-opportunity/           # 经营决策服务
├── legion-os-project/               # 项目管理服务（core_db）
├── legion-os-task/                  # 项目实施服务（core_db）
├── legion-os-workflow/              # 产研流程服务（core_db）
├── legion-os-agent/                 # 数字员工服务
├── legion-os-asset/                 # 技术资产服务
├── legion-os-knowledge/             # 知识经验服务
├── legion-os-infra/                 # 基础设施服务
├── legion-os-iam/                   # 用户权限服务（iam_db）
├── legion-os-evolution/             # 自我进化服务
├── legion-os-valuation/             # 价值评估服务
└── legion-os-portal/                # 个人域BFF服务
```

**每个服务的标准依赖：** Spring Boot Web + Nacos + OpenFeign + AMQP + Actuator + Common模块

### 6.14 API版本控制策略

- **URL版本控制**：`/api/v1/projects/{id}`（当前）→ `/api/v2/projects/{id}`（并行存在≥3个月）
- **事件版本兼容**：payload含`version`字段，消费者忽略未知字段
- **弃用策略**：API标记`@Deprecated`，保留3个月后返回410 Gone

### 6.15 监控与告警

| 类型 | 指标 | 告警规则 |
|------|------|---------|
| 技术 | JVM堆内存、API错误率、队列深度 | 错误率>5%立即告警 |
| 业务 | 商机转化率、任务按时完成率、数字员工利用率 | 转化率<20%预警 |

| 级别 | 场景 | 响应时间 |
|------|------|---------|
| P0 | 核心服务宕机、队列堆积>10000 | 立即 |
| P1 | API错误率>5%、实例故障>3 | 5分钟 |
| P2 | 积分计算延迟>5分钟 | 30分钟 |

---

### 6.16 演进式服务拆分策略

**MVP阶段（Phase 0-1）：4个核心服务 + 1个BFF**

```
┌─────────────────────────────────────────────────────────────┐
│  MVP服务架构（Phase 0-1）                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  pdm-svc   │  │  asset-svc  │  │  agent-svc  │        │
│  │  (核心聚合)  │  │ (资产+知识)  │  │ (数字员工)   │        │
│  │             │  │             │  │  MVP简化     │        │
│  │ opp+prj+tsk │  │ ast+knw+evo │  │ 远程API调用  │        │
│  │ +wf(线性)   │  │ +val(基础)  │  │ 无容器化     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│         │                                              │    │
│         └──────────────────┬───────────────────────────┘    │
│                            │                                │
│                   ┌─────────────┐                          │
│                   │  portal-svc │                          │
│                   │   (BFF)     │                          │
│                   └─────────────┘                          │
│                                                             │
│  支撑服务：Gateway + Nacos + MySQL + RabbitMQ + Redis        │
│  （无Sentinel/SkyWalking/死信队列）                          │
└─────────────────────────────────────────────────────────────┘
```

**MVP阶段服务说明：**
| 服务 | 包含域 | 说明 |
|------|--------|------|
| pdm-svc | 经营决策+项目管理+项目实施+产研流程 | 高频联动，共享core_db本地事务 |
| asset-svc | 技术资产+知识经验+自我进化+价值评估 | 辅助域聚合，降低运维复杂度 |
| agent-svc | 数字员工 | MVP简化：远程LLM API调用，无Body容器化 |
| portal-svc | 个人域(BFF) | 只读聚合，数据来自各服务 |
| iam-svc | 用户权限 | 独立服务，RBAC标准实现 |

**成长期（Phase 2-3）：拆分为8个服务**

按业务复杂度拆分：
- pdm-svc → opp-svc + prj-svc + tsk-svc + wf-svc
- asset-svc → ast-svc + knw-svc + evo-svc + val-svc
- agent-svc 保持独立，引入Body容器化
- 新增 inf-svc（基础设施域）
- 引入 Sentinel + SkyWalking + 死信队列

**成熟期（Phase 4+）：完整12个服务**

按领域模型完整拆分，各服务独立演进：
- 所有服务独立部署
- 完整事件驱动架构
- 支持多组织、多租户
- 数字员工完整运行时（k8s调度、心跳、故障恢复）

**拆分原则：**
1. **按业务复杂度拆分**，不是按域数量平均拆分
2. **高频联动的域先合并**，降低跨服务调用
3. **辅助域可聚合**，减少运维负担
4. **数字员工独立**，技术栈和部署模式特殊
5. **iam-svc始终独立**，用户数据权威源

**人机协同架构哲学：**
> 产研军团OS的架构核心不是"微服务拆分得多细"，而是"人和数字员工是否被同等对待"。
> 
> 统一身份（iam-svc）、统一任务（tsk-svc）、统一评估（val-svc）——这三层是架构的基石。
> 工作流编排（wf-svc）是连接层，让混合编排成为可能。
> 技术资产（ast-svc）和知识经验（knw-svc）是赋能层，让数字员工有知识可学、让人类员工有资产可用。
> 
> 所有技术选型（Spring Cloud、RabbitMQ、core_db Schema隔离）都服务于这一个目标：
> **让"人机协同"从理念变成代码里的一等公民。**

**数据库演进：**
| 阶段 | 数据库实例 | Schema/库 |
|------|-----------|----------|
| MVP | 1个MySQL | core_db（prj+tsk+wf schema）+ iam_db |
| 成长期 | 2个MySQL | core_db拆分 + iam_db + asset_db |
| 成熟期 | 按需拆分 | 各服务独立数据库实例 |

