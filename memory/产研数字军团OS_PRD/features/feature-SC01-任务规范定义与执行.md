# 功能设计文档：SC-01 任务规范的定义与执行

> **对应PRD：** 第5章 SC-01 / 第7章 Week 1 / 第4章 4.3.4 产研流程域
>
> **优先级：** P0
>
> **可演示时间：** 第2周末
>
> **涉及服务：** wf-svc（产研流程域）、tsk-svc（项目实施域）、prj-svc（项目管理域）、opp-svc（经营决策域）、iam-svc（用户权限域）

---

## 1. 功能概述

### 1.1 目标

实现任务规范（Task Spec）的完整生命周期管理：定义 → 发布 → 实例化 → 执行 → 验收。

任务规范是OS的核心抽象，定义"什么人在什么条件下执行什么动作、产出什么、如何验收"。项目规范是任务规范的一种类型（由MRD触发），普通任务规范可独立执行。

### 1.2 范围边界

**MVP内：**
- 任务规范CRUD（6要素表单）
- 线性节点编排（人节点 / 数字员工节点 / 审核节点）
- 任务实例创建与状态流转
- MRD通过后自动触发项目规范实例化
- T1项目驾驶舱工作台、T7 Review面板工作台

**MVP外（延后）：**
- 分支/循环节点（只支持线性顺序执行）
- 子任务规范嵌套（T9.3在SC-02（设计类任务执行）中实现）
- 复杂判定规则（MVP只支持技能匹配+负载均衡）

---

## 2. 用户故事映射

| PRD用户故事 | 本功能覆盖范围 |
|------------|---------------|
| 3.2.1 需求承接与评估 | 接收MRD → 创建项目规范实例 |
| 3.2.2 项目初始化 | 项目创建、里程碑管理（简化） |
| 3.2.4 任务分解与里程碑制定 | 普通任务规范创建、节点编排 |
| 3.4.6 任务规范定义 | 规范CRUD、6要素表单、节点编排 |

---

## 3. 业务流程

### 3.1 任务规范定义流程

```
AI Agent架构师              wf-svc                 tsk-svc
    │                         │                       │
    │── 创建任务规范 ────────→│                       │
    │   （选择类型：项目/普通）  │── 规范草稿存储        │
    │                         │   状态:草稿            │
    │                         │                       │
    │── 填写6要素 ────────────→│                       │
    │   ├── 元数据             │── 节点编排（线性）     │
    │   ├── 输入项/标准        │── 判定规则配置         │
    │   ├── 产出项/验收标准    │                       │
    │   ├── 子任务规范清单     │                       │
    │   ├── 执行岗责任要求     │                       │
    │   └── 执行工作台         │                       │
    │                         │                       │
    │── 发布规范 ─────────────→│                       │
    │                         │── 状态:已发布          │
    │                         │   版本+1              │
    │                         │   历史版本保留         │
```

### 3.2 MRD驱动项目实例化流程

```
经营管理者                opp-svc                prj-svc                wf-svc                tsk-svc
    │                       │                      │                      │                      │
    │── MRD确认通过 ────────→│                      │                      │                      │
    │                       │── 发布MRD通过事件 ───→│                      │                      │
    │                       │                      │── 创建项目            │                      │
    │                       │                      │   状态:已创建         │                      │
    │                       │                      │                      │                      │
    │                       │                      │── 触发项目规范实例化 ──→│                      │
    │                       │                      │                      │── 加载项目规范模板    │
    │                       │                      │                      │── 创建项目规范实例    │
    │                       │                      │                      │   状态:待执行        │
    │                       │                      │                      │                      │
    │                       │                      │                      │── 按节点顺序执行 ─────→│
    │                       │                      │                      │   节点1:待执行       │
```

### 3.3 普通任务规范人工创建流程

```
复合型研发经理            wf-svc                 tsk-svc                iam-svc
    │                       │                      │                      │
    │── 创建普通任务规范 ────→│                      │                      │
    │   （选择父项目规范）     │── 关联父规范          │                      │
    │                       │── 存储任务规范草稿     │                      │
    │                       │                      │                      │
    │── 发布任务规范 ────────→│                      │                      │
    │                       │── 状态:已发布         │                      │
    │                       │                      │                      │
    │── 创建任务实例 ────────→│                      │                      │
    │                       │── 触发实例化 ─────────→│                      │
    │                       │                      │── 任务实例创建        │
    │                       │                      │   状态:待分配        │
    │                       │                      │                      │
    │                       │                      │── 调用判定规则 ───────→│
    │                       │                      │   技能匹配→负载均衡   │
    │                       │                      │←── 分配结果 ──────────│
    │                       │                      │   执行者:人/数字员工  │
    │                       │                      │   状态:待执行        │
```

---

## 4. 数据模型

### 4.1 任务规范（Task Spec）

```java
@Entity
@Table(name = "task_spec", schema = "wf")
public class TaskSpec {
    @Id
    private String specId;           // 规范唯一标识
    private String name;             // 规范名称
    private String version;          // 版本号（发布时+1）
    
    @Enumerated(EnumType.STRING)
    private SpecType type;           // 项目规范 / 普通任务规范 / 子任务规范
    
    @Enumerated(EnumType.STRING)
    private SpecStatus status;       // 草稿 / 已发布 / 已废弃
    
    @OneToOne(cascade = CascadeType.ALL)
    private SpecMetadata metadata;   // 元数据
    
    @OneToOne(cascade = CascadeType.ALL)
    private InputDefinition input;   // 输入项与输入标准
    
    @OneToOne(cascade = CascadeType.ALL)
    private OutputDefinition output; // 产出项与验收标准
    
    @OneToMany(cascade = CascadeType.ALL, orphanRemoval = true)
    @OrderBy("sequence ASC")
    private List<TaskNode> nodes;    // 任务节点序列（线性）
    
    @OneToOne(cascade = CascadeType.ALL)
    private AssignmentRule assignmentRule; // 执行岗判定规则
    
    private String workbenchType;    // 执行工作台类型
    
    private String parentSpecId;     // 父规范ID（普通任务规范→项目规范）
    
    private LocalDateTime createdAt;
    private LocalDateTime publishedAt;
    private String createdBy;
}
```

### 4.2 任务节点（Task Node）

```java
@Entity
@Table(name = "task_node", schema = "wf")
public class TaskNode {
    @Id
    private String nodeId;
    
    private String specId;           // 所属规范ID
    private Integer sequence;        // 节点顺序（线性执行）
    private String name;             // 节点名称
    
    @Enumerated(EnumType.STRING)
    private NodeType type;           // 人节点 / 数字员工节点 / 审核节点
    
    private String skillRequirement; // 技能要求（用于判定规则）
    private String inputMapping;     // 输入映射（JSON：从前序节点获取数据）
    private String outputMapping;    // 输出映射（JSON：产出数据传递给后续）
    
    @Enumerated(EnumType.STRING)
    private NodeStatus status;       // 待执行 / 执行中 / 已完成 / 已跳过
}
```

### 4.3 任务实例（Task Instance）

```java
@Entity
@Table(name = "task_instance", schema = "tsk")
public class TaskInstance {
    @Id
    private String instanceId;
    
    private String specId;           // 关联规范ID
    private String specVersion;      // 规范版本（实例化时锁定）
    
    @Enumerated(EnumType.STRING)
    private InstanceType type;       // 项目实例 / 普通任务实例
    
    @Enumerated(EnumType.STRING)
    private InstanceStatus status;   // 待执行 / 执行中 / 待审核 / 已完成 / 已终止
    
    private String projectId;        // 关联项目ID（普通任务实例）
    private String parentInstanceId; // 父实例ID（普通任务实例→项目实例）
    
    @OneToMany(cascade = CascadeType.ALL, orphanRemoval = true)
    @OrderBy("sequence ASC")
    private List<NodeInstance> nodeInstances; // 节点实例序列
    
    private String currentNodeId;    // 当前执行节点ID
    private String assignedTo;       // 当前执行者（用户ID/数字员工实例ID）
    
    private LocalDateTime startedAt;
    private LocalDateTime completedAt;
}
```

---

## 5. 状态机

### 5.1 任务规范状态机

```
┌─────────┐    创建     ┌─────────┐    发布      ┌─────────┐    更新     ┌─────────┐
│  草稿   │ ─────────→ │  草稿   │ ─────────→ │  已发布  │ ─────────→ │  已发布  │
│ (draft) │            │ (draft) │            │(published)│           │(published)│
└─────────┘            └─────────┘            └────┬────┘            └────┬────┘
     ▲                                              │                      │
     │                                              │                      │
     └──────────────────────────────────────────────┘                      │
                  废弃（保留历史版本）                                        │
                                                                           │
                                                                           ▼
                                                                    ┌─────────┐
                                                                    │  已废弃  │
                                                                    │(deprecated)
                                                                    └─────────┘
```

**状态规则：**
- 草稿 → 已发布：必须填写完整6要素，至少1个节点
- 已发布 → 已发布（新版本）：创建新版本，旧版本保留只读
- 已发布 → 已废弃：不影响已创建的实例

### 5.2 任务实例状态机

```
┌─────────┐    实例化    ┌─────────┐    开始执行    ┌─────────┐    节点完成    ┌─────────┐
│  待执行  │ ─────────→ │  执行中  │ ───────────→ │  执行中  │ ───────────→ │  待审核  │
│(pending)│            │(running) │   首个节点     │(running) │   有审核节点   │(review) │
└─────────┘            └────┬────┘              └────┬────┘              └────┬────┘
                            │                        │                        │
                            │    所有节点完成        │    无审核节点          │    审核通过
                            │    ┌─────────┐        │    ┌─────────┐        │    ┌─────────┐
                            └──→ │  已完成  │        └──→ │  已完成  │        └──→ │  已完成  │
                                 │(completed)│            │(completed)│            │(completed)│
                                 └─────────┘            └─────────┘            └─────────┘
```

**状态规则：**
- 待执行 → 执行中：首个节点被触发
- 执行中 → 待审核：节点完成且下一节点是审核节点
- 待审核 → 执行中：审核通过，继续下一节点
- 待审核 → 执行中（回退）：审核拒绝，返回上一节点重新执行
- 任意状态 → 已终止：人工终止实例

---

## 6. API设计

### 6.1 任务规范管理

```yaml
# 创建任务规范（草稿）
POST /api/v1/task-specs
Request:
  name: "MRD驱动的Java项目"
  type: "PROJECT"
  metadata: { ... }
  input: { ... }
  output: { ... }
  nodes: [
    { sequence: 1, name: "需求确认", type: "HUMAN", skillRequirement: "产品经理" },
    { sequence: 2, name: "架构设计", type: "HUMAN", skillRequirement: "架构师" },
    { sequence: 3, name: "代码开发", type: "AGENT", skillRequirement: "Java开发" },
    { sequence: 4, name: "代码Review", type: "HUMAN", skillRequirement: "技术负责人" }
  ]
  assignmentRule: { ... }
  workbenchType: "PROJECT_COCKPIT"
Response:
  specId: "spec-xxx"
  status: "DRAFT"

# 发布任务规范
POST /api/v1/task-specs/{specId}/publish
Response:
  specId: "spec-xxx"
  version: "1.0.0"
  status: "PUBLISHED"

# 获取任务规范详情
GET /api/v1/task-specs/{specId}
Response:
  specId: "spec-xxx"
  name: "MRD驱动的Java项目"
  version: "1.0.0"
  status: "PUBLISHED"
  nodes: [ ... ]
  # 完整6要素

# 创建任务实例
POST /api/v1/task-instances
Request:
  specId: "spec-xxx"
  type: "PROJECT"
  contextData: { mrdId: "mrd-xxx", projectName: "xxx" }
Response:
  instanceId: "inst-xxx"
  status: "PENDING"
  currentNode: { nodeId: "node-1", name: "需求确认", status: "PENDING" }
```

### 6.2 节点执行

```yaml
# 获取当前节点任务
GET /api/v1/task-instances/{instanceId}/current-node
Response:
  nodeId: "node-1"
  name: "需求确认"
  type: "HUMAN"
  status: "PENDING"
  inputData: { ... }
  workbenchUrl: "/workbench/project-cockpit/{instanceId}"

# 提交节点执行结果
POST /api/v1/task-instances/{instanceId}/nodes/{nodeId}/complete
Request:
  outputData: { ... }
  deliverables: ["doc-xxx", "code-xxx"]
Response:
  instanceId: "inst-xxx"
  status: "RUNNING"
  nextNode: { nodeId: "node-2", name: "架构设计", status: "PENDING" }

# 审核节点审批
POST /api/v1/task-instances/{instanceId}/nodes/{nodeId}/review
Request:
  action: "APPROVE" | "REJECT"
  comment: "..."
Response:
  instanceId: "inst-xxx"
  status: "RUNNING" | "RUNNING"  # APPROVE→继续, REJECT→回退
  nextNode: { ... }
```

---

## 7. 事件设计

| 事件名称 | 发布者 | 订阅者 | 触发条件 |
|---------|--------|--------|---------|
| `TaskSpec.Published` | wf-svc | tsk-svc, prj-svc | 规范发布 |
| `TaskInstance.Created` | tsk-svc | wf-svc, prj-svc | 实例创建 |
| `TaskInstance.NodeStarted` | tsk-svc | wf-svc, agt-svc | 节点开始执行 |
| `TaskInstance.NodeCompleted` | tsk-svc | wf-svc, prj-svc | 节点完成 |
| `TaskInstance.ReviewRequested` | tsk-svc | iam-svc（通知） | 进入审核节点 |
| `TaskInstance.Completed` | tsk-svc | prj-svc, val-svc | 实例完成 |
| `MRD.Approved` | opp-svc | prj-svc, wf-svc | MRD审批通过 |

---

## 8. 工作台设计

### 8.1 T1 项目驾驶舱（Project Cockpit）

```
项目驾驶舱（T1工作台）
├── 顶部：项目信息
│   ├── 项目名称 + 状态标签
│   ├── MRD摘要（点击展开完整MRD）
│   └── 当前阶段 + 进度百分比
├── 左侧：里程碑看板
│   ├── 里程碑列表（时间轴）
│   ├── 当前里程碑高亮
│   └── 延期预警（红色标记）
├── 中部：任务列表
│   ├── 任务卡片（名称/负责人/状态/截止时间）
│   ├── 点击展开任务详情
│   └── 筛选：全部/进行中/已完成/阻塞
├── 右侧：进度追踪
│   ├── 甘特图（简化版）
│   ├── 完成率统计
│   └── 风险项列表
└── 底部：操作栏
    ├── 新建任务
    ├── 调整里程碑
    └── 导出报告
```

**OS内功能：** 项目信息展示、里程碑管理、任务列表、进度统计
**OS外交互：** MRD编写在经营决策域完成，代码开发在本地IDE完成

### 8.2 T7 Review面板（Review Panel）

```
Review面板（T7工作台）
├── 顶部：Review信息
│   ├── 代码提交信息（作者/时间/分支）
│   ├── 关联任务
│   └── Review状态（待Review/进行中/已通过/已拒绝）
├── 左侧：文件列表
│   ├── 变更文件树
│   ├── 点击跳转对应Diff
│   └── 文件状态（新增/修改/删除）
├── 中部：Diff查看
│   ├── 分屏对比（旧/新）
│   ├── 行级批注（点击行号添加评论）
│   └── 语法高亮
├── 右侧：规范检查
│   ├── 自动检查结果（代码规范/安全扫描）
│   ├── 问题列表（严重程度分级）
│   └── 一键修复建议
└── 底部：操作栏
    ├── Approve（通过）
    ├── Reject（拒绝+填写原因）
    ├── Request Changes（要求修改）
    └── 添加整体评论
```

**OS内功能：** Diff查看、行级批注、规范检查、Approve/Reject
**OS外交互：** 无，全流程OS内完成

---

## 9. 验收标准

### 9.1 功能验收

- [ ] 能定义任务规范（含完整6要素）
- [ ] 能进行线性节点编排（人/数字员工/审核节点）
- [ ] 能发布任务规范（版本+1，历史保留）
- [ ] MRD通过后自动触发项目规范实例化
- [ ] 项目规范实例按节点顺序执行
- [ ] 普通任务规范可由人工创建并实例化
- [ ] 任务分配按判定规则执行（技能匹配→负载→人）
- [ ] 节点执行完成后自动流转到下一节点
- [ ] 审核节点支持Approve/Reject/Request Changes
- [ ] 任务实例状态实时可见

### 9.2 工作台验收

- [ ] T1项目驾驶舱可打开并展示项目信息、里程碑、任务列表
- [ ] T7 Review面板可打开并展示Diff、支持行级批注、Approve/Reject
- [ ] 工作台数据与后端状态实时同步

### 9.3 性能验收

- [ ] 任务规范CRUD接口响应时间 < 500ms
- [ ] 任务实例状态查询响应时间 < 200ms
- [ ] 节点流转延迟 < 1s（同步调用）

---

## 10. 依赖关系

| 依赖项 | 类型 | 说明 |
|--------|------|------|
| iam-svc | 强依赖 | 用户认证、权限校验 |
| opp-svc | 强依赖 | MRD状态、触发项目创建 |
| prj-svc | 强依赖 | 项目信息、里程碑数据 |
| tsk-svc | 强依赖 | 任务实例、节点执行 |
| agt-svc | 弱依赖 | 数字员工节点执行（Week 2接入） |

---

## 11. 风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| 节点编排UI复杂度高 | Week 1交付延期 | MVP先做表单式节点列表，可视化拖拽延后 |
| MRD→项目实例化链路长 | 联调困难 | Day 3-4先完成后端链路，Day 5前端联调 |
| 判定规则过于简单 | 演示效果差 | 预设几组典型规则（Java开发→AI工程师/数字员工） |

---

## 12. 变更记录

| 日期 | 内容 | 作者 |
|------|------|------|
| 2025-06-01 | 初稿（工作流规范版） | Hermes |
| 2025-06-01 | 重构：工作流规范→任务规范，项目规范是任务规范的一种类型 | Hermes |