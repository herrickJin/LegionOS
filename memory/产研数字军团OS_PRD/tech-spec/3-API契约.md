# 技术方案：3. API契约（MVP版）

> **对应PRD：** 第4章 领域模型 + feature-SC01 功能设计
>
> **目标：** 定义MVP阶段所有服务的RESTful API，供前后端开发使用
>
> **规范：** URL版本控制 /api/v1/，统一响应格式，YAML契约

---

## 1. 统一响应格式

```yaml
# 成功响应
{
  "code": 200,
  "message": "success",
  "data": { ... },
  "timestamp": 1705312800000,
  "traceId": "trace-uuid-v7"
}

# 错误响应
{
  "code": 400,
  "message": "参数错误：name不能为空",
  "data": null,
  "timestamp": 1705312800000,
  "traceId": "trace-uuid-v7"
}

# 分页响应
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [ ... ],
    "total": 100,
    "page": 1,
    "size": 20
  },
  "timestamp": 1705312800000,
  "traceId": "trace-uuid-v7"
}
```

---

## 2. core-svc API

### 2.1 经营决策域（opp）

```yaml
# 商机管理
POST   /api/v1/opportunities              # 创建商机
GET    /api/v1/opportunities              # 商机列表（分页+筛选）
GET    /api/v1/opportunities/{id}         # 商机详情
PUT    /api/v1/opportunities/{id}         # 更新商机
POST   /api/v1/opportunities/{id}/archive # 归档商机

# 可行性报告
POST   /api/v1/feasibility-reports        # 创建报告
GET    /api/v1/feasibility-reports/{id}   # 报告详情
PUT    /api/v1/feasibility-reports/{id}   # 更新报告
POST   /api/v1/feasibility-reports/{id}/approve  # 审批通过
POST   /api/v1/feasibility-reports/{id}/reject   # 审批拒绝

# MRD管理
POST   /api/v1/mrds                      # 创建MRD
GET    /api/v1/mrds                      # MRD列表
GET    /api/v1/mrds/{id}                 # MRD详情
PUT    /api/v1/mrds/{id}                 # 更新MRD
POST   /api/v1/mrds/{id}/submit          # 提交评审
POST   /api/v1/mrds/{id}/approve         # 审批通过（触发项目创建事件）
POST   /api/v1/mrds/{id}/reject          # 审批拒绝
POST   /api/v1/mrds/{id}/archive         # 归档
```

### 2.2 项目管理域（prj）

```yaml
# 项目管理
POST   /api/v1/projects                  # 创建项目（MRD通过后自动调用）
GET    /api/v1/projects                  # 项目列表
GET    /api/v1/projects/{id}             # 项目详情
PUT    /api/v1/projects/{id}             # 更新项目
POST   /api/v1/projects/{id}/start       # 启动项目
POST   /api/v1/projects/{id}/pause       # 暂停项目
POST   /api/v1/projects/{id}/archive     # 归档项目

# 里程碑
POST   /api/v1/projects/{projectId}/milestones      # 创建里程碑
GET    /api/v1/projects/{projectId}/milestones      # 里程碑列表
PUT    /api/v1/projects/{projectId}/milestones/{id} # 更新里程碑
POST   /api/v1/milestones/{id}/complete             # 标记完成

# 风险项
POST   /api/v1/projects/{projectId}/risks  # 创建风险项
GET    /api/v1/projects/{projectId}/risks  # 风险列表
PUT    /api/v1/risks/{id}                  # 更新风险
POST   /api/v1/risks/{id}/mitigate         # 标记已缓解

# 变更记录
POST   /api/v1/projects/{projectId}/changes  # 创建变更
GET    /api/v1/projects/{projectId}/changes  # 变更列表
POST   /api/v1/changes/{id}/approve          # 审批变更
```

### 2.3 项目实施域（tsk）

```yaml
# 任务实例管理
POST   /api/v1/task-instances             # 创建任务实例
GET    /api/v1/task-instances             # 任务实例列表
GET    /api/v1/task-instances/{id}        # 任务实例详情
POST   /api/v1/task-instances/{id}/start  # 开始执行
POST   /api/v1/task-instances/{id}/terminate # 终止实例

# 节点执行
GET    /api/v1/task-instances/{instanceId}/current-node  # 获取当前节点
POST   /api/v1/task-instances/{instanceId}/nodes/{nodeId}/complete  # 完成节点
POST   /api/v1/task-instances/{instanceId}/nodes/{nodeId}/review    # 审核节点

# 交付物
POST   /api/v1/task-instances/{instanceId}/deliverables  # 提交交付物
GET    /api/v1/task-instances/{instanceId}/deliverables  # 交付物列表
PUT    /api/v1/deliverables/{id}                         # 更新交付物
POST   /api/v1/deliverables/{id}/accept                  # 验收通过

# 执行评价
POST   /api/v1/task-instances/{instanceId}/evaluations   # 提交评价
GET    /api/v1/task-instances/{instanceId}/evaluations   # 评价列表
```

### 2.4 产研流程域（wf）

```yaml
# 任务规范管理
POST   /api/v1/task-specs                 # 创建任务规范（草稿）
GET    /api/v1/task-specs                 # 规范列表
GET    /api/v1/task-specs/{id}            # 规范详情
PUT    /api/v1/task-specs/{id}            # 更新规范
POST   /api/v1/task-specs/{id}/publish    # 发布规范（版本+1）
POST   /api/v1/task-specs/{id}/deprecate  # 停用规范

# 任务节点管理
POST   /api/v1/task-specs/{specId}/nodes  # 添加节点
PUT    /api/v1/task-specs/{specId}/nodes/{id}  # 更新节点
DELETE /api/v1/task-specs/{specId}/nodes/{id}  # 删除节点
POST   /api/v1/task-specs/{specId}/nodes/reorder  # 重排节点顺序

# 工作台
GET    /api/v1/workbenches                # 工作台列表
GET    /api/v1/workbenches/{type}         # 工作台详情
GET    /api/v1/workbenches/{type}/render  # 渲染工作台（返回配置+数据）
```

---

## 3. iam-svc API

```yaml
# 认证
POST   /api/v1/auth/login                 # 登录（返回JWT）
POST   /api/v1/auth/logout                # 登出
POST   /api/v1/auth/refresh               # 刷新Token
POST   /api/v1/agents/authenticate        # 数字员工认证（API Key）

# 用户管理
POST   /api/v1/users                      # 创建用户
GET    /api/v1/users                      # 用户列表
GET    /api/v1/users/{id}                 # 用户详情
PUT    /api/v1/users/{id}                 # 更新用户
DELETE /api/v1/users/{id}                 # 删除用户
POST   /api/v1/users/{id}/disable         # 禁用用户

# 角色权限
GET    /api/v1/roles                      # 角色列表
GET    /api/v1/roles/{code}/permissions   # 角色权限
POST   /api/v1/users/{userId}/roles       # 分配角色
DELETE /api/v1/users/{userId}/roles/{code} # 移除角色

# 组织
GET    /api/v1/orgs                       # 组织列表
GET    /api/v1/orgs/{id}                  # 组织详情
GET    /api/v1/orgs/{id}/users            # 组织用户列表
```

---

## 4. agent-svc API

```yaml
# 原型管理
POST   /api/v1/agent-prototypes           # 创建原型
GET    /api/v1/agent-prototypes           # 原型列表
GET    /api/v1/agent-prototypes/{id}      # 原型详情
PUT    /api/v1/agent-prototypes/{id}      # 更新原型
POST   /api/v1/agent-prototypes/{id}/publish    # 发布原型
POST   /api/v1/agent-prototypes/{id}/deprecate  # 废弃原型

# 实例管理
POST   /api/v1/agent-instances            # 创建实例（实例化）
GET    /api/v1/agent-instances            # 实例列表
GET    /api/v1/agent-instances/{id}       # 实例详情
POST   /api/v1/agent-instances/{id}/assign      # 分配任务
POST   /api/v1/agent-instances/{id}/release     # 释放任务
POST   /api/v1/agent-instances/{id}/recycle     # 回收实例

# 执行
POST   /api/v1/agent-instances/{id}/execute     # 执行任务
GET    /api/v1/agent-instances/{id}/logs        # 执行日志

# 灵魂配置
GET    /api/v1/agent-prototypes/{id}/soul       # 获取灵魂配置
PUT    /api/v1/agent-prototypes/{id}/soul       # 更新灵魂配置
```

---

## 5. asset-svc API

```yaml
# 技术资产
POST   /api/v1/assets                     # 创建资产
GET    /api/v1/assets                     # 资产列表
GET    /api/v1/assets/{id}                # 资产详情
PUT    /api/v1/assets/{id}                # 更新资产
POST   /api/v1/assets/{id}/publish        # 发布资产
POST   /api/v1/assets/{id}/reuse          # 记录复用

# 知识条目
POST   /api/v1/knowledges                 # 创建知识
GET    /api/v1/knowledges                 # 知识列表
GET    /api/v1/knowledges/{id}            # 知识详情
PUT    /api/v1/knowledges/{id}            # 更新知识
POST   /api/v1/knowledges/{id}/cite       # 记录引用
GET    /api/v1/knowledges/search          # 全文检索

# 改进需求
POST   /api/v1/improvements               # 创建改进需求
GET    /api/v1/improvements               # 改进列表
GET    /api/v1/improvements/{id}          # 改进详情
PUT    /api/v1/improvements/{id}          # 更新改进
POST   /api/v1/improvements/{id}/close    # 关闭改进

# 价值积分
GET    /api/v1/points                     # 积分列表
GET    /api/v1/points/{ownerId}           # 个人积分
GET    /api/v1/points/summary             # 积分汇总
POST   /api/v1/points/calculate           # 触发积分计算（内部）

# 价值规则
GET    /api/v1/point-rules                # 规则列表
GET    /api/v1/point-rules/current        # 当前生效规则
POST   /api/v1/point-rules                # 创建规则
PUT    /api/v1/point-rules/{id}           # 更新规则
POST   /api/v1/point-rules/{id}/enable    # 启用规则
```

---

## 6. portal-svc API（BFF）

```yaml
# 个人工作台
GET    /api/v1/portal/dashboard           # 个人仪表盘
GET    /api/v1/portal/todos               # 我的待办
GET    /api/v1/portal/tasks               # 我的任务
GET    /api/v1/portal/messages            # 我的消息
GET    /api/v1/portal/projects            # 我的项目
GET    /api/v1/portal/assets              # 我的资产

# 工作台渲染
GET    /api/v1/portal/workbench/{type}    # 渲染工作台
POST   /api/v1/portal/workbench/{type}/action  # 工作台操作
```

---

## 7. 详细契约示例

### 7.1 创建任务规范

```yaml
POST /api/v1/task-specs
Request:
  headers:
    Authorization: Bearer {jwt}
    Content-Type: application/json
  body:
    name: "MRD驱动的Java项目"
    type: "PROJECT"
    metadata:
      category: "软件开发"
      tags: ["Java", "SpringBoot"]
      owner: "user-001"
    inputDefinition:
      items:
        - name: "MRD文档"
          type: "DOCUMENT"
          required: true
        - name: "技术约束"
          type: "TEXT"
          required: false
      standards:
        - "MRD必须通过审批"
        - "技术约束需明确JDK版本"
    outputDefinition:
      items:
        - name: "代码PR"
          type: "CODE"
          required: true
        - name: "单元测试报告"
          type: "REPORT"
          required: true
      acceptanceCriteria:
        - "代码覆盖率≥80%"
        - "通过代码Review"
    assignmentRule:
      strategy: "SKILL_MATCH"
      fallback: "LOAD_BALANCE"
      defaultAssignee: null
    workbenchType: "PROJECT_COCKPIT"
    nodes:
      - sequence: 1
        name: "需求确认"
        type: "HUMAN"
        skillRequirement: "产品经理"
      - sequence: 2
        name: "架构设计"
        type: "HUMAN"
        skillRequirement: "架构师"
      - sequence: 3
        name: "代码开发"
        type: "AGENT"
        skillRequirement: "Java开发"
      - sequence: 4
        name: "代码Review"
        type: "HUMAN"
        skillRequirement: "技术负责人"

Response 200:
  code: 200
  message: "success"
  data:
    id: "spec-001"
    name: "MRD驱动的Java项目"
    type: "PROJECT"
    status: "DRAFT"
    version: "1.0.0"
    createdAt: "2025-06-01T10:00:00Z"
```

### 7.2 发布任务规范

```yaml
POST /api/v1/task-specs/{specId}/publish
Response 200:
  code: 200
  message: "success"
  data:
    id: "spec-001"
    status: "PUBLISHED"
    version: "1.0.0"
    publishedAt: "2025-06-01T12:00:00Z"

Response 400:
  code: 400
  message: "发布失败：节点列表为空"
```

### 7.3 MRD审批通过（触发项目创建）

```yaml
POST /api/v1/mrds/{mrdId}/approve
Request:
  body:
    comment: "技术可行，资源充足，同意立项"

Response 200:
  code: 200
  message: "success"
  data:
    mrdId: "mrd-001"
    status: "已通过"
    approvedBy: "user-001"
    approvedAt: "2025-06-01T14:00:00Z"
    projectId: "proj-001"  # 自动创建的项目ID
```

### 7.4 获取当前节点任务

```yaml
GET /api/v1/task-instances/{instanceId}/current-node
Response 200:
  code: 200
  message: "success"
  data:
    nodeId: "node-1"
    name: "需求确认"
    type: "HUMAN"
    status: "PENDING"
    inputData:
      mrdSummary: "..."
      requirements: [...]
    workbenchUrl: "/workbench/project-cockpit/inst-001"
```

### 7.5 提交节点执行结果

```yaml
POST /api/v1/task-instances/{instanceId}/nodes/{nodeId}/complete
Request:
  body:
    outputData:
      confirmedRequirements: [...]
      changeLog: "..."
    deliverables:
      - name: "需求确认文档"
        type: "DOCUMENT"
        storagePath: "/docs/requirement-confirmed.md"

Response 200:
  code: 200
  message: "success"
  data:
    instanceId: "inst-001"
    status: "RUNNING"
    nextNode:
      nodeId: "node-2"
      name: "架构设计"
      status: "PENDING"
```

### 7.6 审核节点审批

```yaml
POST /api/v1/task-instances/{instanceId}/nodes/{nodeId}/review
Request:
  body:
    action: "APPROVE"  # APPROVE / REJECT / REQUEST_CHANGES
    comment: "代码质量良好，符合规范"

Response 200 (APPROVE):
  code: 200
  message: "success"
  data:
    instanceId: "inst-001"
    status: "RUNNING"
    nextNode:
      nodeId: "node-3"
      name: "代码开发"
      status: "PENDING"

Response 200 (REJECT):
  code: 200
  message: "success"
  data:
    instanceId: "inst-001"
    status: "RUNNING"
    nextNode:
      nodeId: "node-2"
      name: "架构设计"
      status: "PENDING"  # 回退到上一节点
```

---

## 8. 错误码定义

| 错误码 | 说明 | 场景 |
|--------|------|------|
| 200 | 成功 | 正常响应 |
| 400 | 参数错误 | 请求参数校验失败 |
| 401 | 未认证 | Token缺失或无效 |
| 403 | 无权限 | 权限不足 |
| 404 | 资源不存在 | 查询的记录不存在 |
| 409 | 资源冲突 | 状态冲突（如重复发布） |
| 422 | 业务校验失败 | 业务规则校验失败 |
| 429 | 请求过于频繁 | 限流触发 |
| 500 | 服务器错误 | 内部异常 |
| 503 | 服务不可用 | 下游服务熔断 |

---

## 9. 分页规范

```yaml
# 请求
GET /api/v1/task-specs?page=1&size=20&sort=createdAt,desc

# 响应
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [...],
    "total": 100,
    "page": 1,
    "size": 20,
    "pages": 5
  }
}
```

---

## 10. 筛选规范

```yaml
# 通用筛选参数
GET /api/v1/task-specs?status=PUBLISHED&type=PROJECT&orgId=org-001

# 时间范围
GET /api/v1/task-instances?startDate=2025-06-01&endDate=2025-06-30

# 模糊搜索
GET /api/v1/projects?keyword=Java

# 多选
GET /api/v1/tasks?status=PENDING,RUNNING
```

---

*本文档为MVP阶段API契约，后续版本演进遵循PRD第6章API版本控制策略*
