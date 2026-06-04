#!/usr/bin/env python3
"""Generate the panoramic architecture diagram for 产研数字军团OS."""

import json
import random

# ── Color palette (from color-palette.md) ──
BG = "#FFFFFF"
NEUTRAL_FILL = "#F8FAFC"
NEUTRAL_STROKE = "#334155"
DATA_FILL = "#F0F9FF"
DATA_STROKE = "#026AA2"
AI_FILL = "#F5F3FF"
AI_STROKE = "#7A5AF8"
EXT_FILL = "#F4F3FF"
EXT_STROKE = "#6941C6"
DECISION_FILL = "#FFF7ED"
DECISION_STROKE = "#C4320A"
PRIMARY_TEXT = "#111827"
SECONDARY_TEXT = "#475467"
TERTIARY_TEXT = "#667085"
DIVIDER = "#D0D5DD"

seed_counter = 1000

def sid(prefix):
    global seed_counter
    seed_counter += 1
    return f"{prefix}_{seed_counter}"

def make_rect(uid, x, y, w, h, fill=NEUTRAL_FILL, stroke=NEUTRAL_STROKE, sw=2, rd=8):
    return {
        "id": uid, "type": "rectangle",
        "x": x, "y": y, "width": w, "height": h,
        "strokeColor": stroke, "backgroundColor": fill,
        "fillStyle": "solid", "strokeWidth": sw, "strokeStyle": "solid",
        "roughness": 0, "opacity": 100, "angle": 0,
        "roundness": {"type": 3} if rd else None,
        "seed": seed_counter + 1, "version": 1, "versionNonce": seed_counter + 2,
        "isDeleted": False, "boundElements": [], "updated": 0, "link": None, "locked": False
    }

def make_text(uid, x, y, w, h, text, fs=14, color=PRIMARY_TEXT, align="left", bold=False, fm=3):
    return {
        "id": uid, "type": "text",
        "x": x, "y": y, "width": w, "height": h,
        "text": text, "fontSize": fs, "fontFamily": fm,
        "textAlign": align, "verticalAlign": "middle",
        "strokeColor": color, "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 1, "roughness": 0, "opacity": 100,
        "angle": 0, "seed": seed_counter + 1, "version": 1, "versionNonce": seed_counter + 2,
        "isDeleted": False, "boundElements": None, "updated": 0, "link": None, "locked": False,
        "containerId": None, "originalText": text, "lineHeight": 1.25
    }

def make_arrow(uid, x, y, points, stroke=SECONDARY_TEXT, sw=2):
    return {
        "id": uid, "type": "arrow",
        "x": x, "y": y, "width": max(p[0] for p in points), "height": max(p[1] for p in points),
        "strokeColor": stroke, "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": sw, "strokeStyle": "solid",
        "roughness": 0, "opacity": 100, "angle": 0,
        "seed": seed_counter + 1, "version": 1, "versionNonce": seed_counter + 2,
        "isDeleted": False, "boundElements": None, "updated": 0, "link": None, "locked": False,
        "points": points, "startBinding": None, "endBinding": None,
        "startArrowhead": None, "endArrowhead": "arrow"
    }

def make_line(uid, x1, y1, x2, y2, stroke=DIVIDER, sw=1, dashed=False):
    arr = make_arrow(uid, x1, y1, [[0, 0], [x2-x1, y2-y1]], stroke=stroke, sw=sw)
    arr["endArrowhead"] = None
    if dashed:
        arr["strokeStyle"] = "dashed"
    return arr

def make_dashed_rect(uid, x, y, w, h, fill="transparent", stroke=DIVIDER, sw=1):
    r = make_rect(uid, x, y, w, h, fill=fill, stroke=stroke, sw=sw)
    r["strokeStyle"] = "dashed"
    return r

def make_rounded_rect(uid, x, y, w, h, fill=NEUTRAL_FILL, stroke=NEUTRAL_STROKE, sw=2):
    r = make_rect(uid, x, y, w, h, fill=fill, stroke=stroke, sw=sw)
    r["roundness"] = {"type": 3}
    return r

elements = []

# ============================================================
# CANVAS: 1600 x 2200
# ============================================================

# ── LAYER 1: CLIENT (y: 40 ~ 420) ──

# Client container
elements.append(make_rounded_rect(sid("client_box"), 80, 50, 1440, 350,
                                   fill="#FAFBFC", stroke=DIVIDER, sw=2))

# Layer title
elements.append(make_text(sid("layer1_title"), 100, 56, 500, 30,
                          "终端用户层 — 一个产品 · 四角色视图", fs=18, color=PRIMARY_TEXT, bold=True))

# Four role views
view_w = 320
view_h = 210
view_y = 100
gap = 30
start_x = 110

role_data = [
    ("经营管理者", "经营看板 · 商机洞察 · 审批中心", NEUTRAL_FILL, NEUTRAL_STROKE),
    ("复合型研发经理", "项目管理 · 需求/任务看板 · 进度追踪", NEUTRAL_FILL, NEUTRAL_STROKE),
    ("AI 工程师", "个人工作台 · 任务执行 · 数字员工协同 · 流式预览", AI_FILL, AI_STROKE),
    ("AI Agent 架构师", "流程规范管理 · 数字员工管理\n组织与权限 · 系统配置 · 运维监控", DECISION_FILL, DECISION_STROKE),
]

for i, (title, desc, fill, stroke) in enumerate(role_data):
    vx = start_x + i * (view_w + gap)
    # View box
    elements.append(make_rounded_rect(sid(f"view{i}_box"), vx, view_y, view_w, view_h,
                                       fill=fill, stroke=stroke, sw=1.5))
    # View title
    elements.append(make_text(sid(f"view{i}_title"), vx + 10, view_y + 6, view_w - 20, 28,
                              title, fs=15, color=stroke, bold=True))
    # Separator line
    elements.append(make_line(sid(f"view{i}_sep"), vx + 10, view_y + 38, vx + view_w - 10, view_y + 38))
    # Description
    elements.append(make_text(sid(f"view{i}_desc"), vx + 14, view_y + 50, view_w - 28, view_h - 60,
                              desc, fs=12, color=SECONDARY_TEXT))

# Shared modules bar
shared_y = view_y + view_h + 20
elements.append(make_rounded_rect(sid("shared_bar"), start_x, shared_y, 1360, 32,
                                   fill="#F1F5F9", stroke=DIVIDER, sw=1))
elements.append(make_text(sid("shared_text"), start_x + 10, shared_y, 1340, 32,
                          "共用模块：消息中心  |  项目切换  |  个人设置  |  通知",
                          fs=13, color=TERTIARY_TEXT, align="left"))

# Mobile (dashed, growth phase)
mx = start_x + 4 * (view_w + gap) + 20
mobile_x = mx
mobile_y = view_y + view_h + 70
elements.append(make_dashed_rect(sid("mobile_box"), mobile_x, mobile_y, 180, 38,
                                  fill="#F8FAFC", stroke=DIVIDER, sw=1))
elements.append(make_text(sid("mobile_text"), mobile_x + 10, mobile_y, 160, 38,
                          "📱 移动端（成长期）", fs=12, color=TERTIARY_TEXT))

# Interaction labels below client
inter_y = 410
elements.append(make_text(sid("inter_label"), 100, inter_y, 1440, 22,
                          "HTTPS + REST API + SSE  ·  JWT Token 统一认证  ·  Gateway 鉴权路由  ·  路由懒加载",
                          fs=13, color=TERTIARY_TEXT, align="center"))

# ============================================================
# CHANNEL 1 BAR (y: 440 ~ 480)
# ============================================================
ch1_y = 440
elements.append(make_rounded_rect(sid("ch1_bar"), 80, ch1_y, 1440, 40,
                                   fill="#E0F2FE", stroke="#0284C7", sw=1.5))
elements.append(make_text(sid("ch1_label"), 100, ch1_y + 2, 200, 36,
                          "通道 1：", fs=13, color="#0284C7", bold=True))
elements.append(make_text(sid("ch1_detail"), 210, ch1_y + 2, 1280, 36,
                          "HTTPS + REST API + SSE  —  JWT Token  —  Gateway 统一鉴权  —  四角色走同一入口，iam-svc 按 RBAC 控制可见视图",
                          fs=12, color=SECONDARY_TEXT))

# ============================================================
# LAYER 2: SERVER (y: 500 ~ 1500)
# ============================================================

# Server container
svr_x, svr_y, svr_w, svr_h = 80, 500, 1440, 980
elements.append(make_rounded_rect(sid("server_box"), svr_x, svr_y, svr_w, svr_h,
                                   fill="#F8FAFC", stroke=DIVIDER, sw=2))
elements.append(make_text(sid("svr_title"), 100, svr_y + 6, 300, 30,
                          "OS 服务端（Microservices）", fs=18, color=PRIMARY_TEXT, bold=True))

# ── 2a: Gateway ──
gw_y = svr_y + 45
gw_w = 500
gw_x = (svr_x + svr_w // 2) - gw_w // 2
elements.append(make_rounded_rect(sid("gw_box"), gw_x, gw_y, gw_w, 56,
                                   fill="#F0FDF4", stroke="#059669", sw=1.5))
elements.append(make_text(sid("gw_title"), gw_x + 15, gw_y + 4, gw_w - 30, 22,
                          "gateway-svc（端口 8085）— 技术网关", fs=14, color="#059669", bold=True))
elements.append(make_text(sid("gw_desc"), gw_x + 15, gw_y + 26, gw_w - 30, 24,
                          "JWT 验签  |  路由分发  |  限流熔断  |  WebSocket 升级  |  依赖 Redis（限流计数 / JWT 黑名单）",
                          fs=12, color=SECONDARY_TEXT))

# ── 2b: Business Services ──
bs_y = gw_y + 90
bs_card_w = 320
bs_card_h = 340
bs_gap = 30
bs_start_x = svr_x + 40

svc_data = [
    {
        "id": "pdm", "name": "pdm-svc", "port": "8080", "color": "#175CD3",
        "title": "核心业务服务",
        "items": ["经营决策", "项目管理", "项目实施"],
        "db": "PostgreSQL（JSONB）",
        "fill": "#EFF8FF", "stroke": "#175CD3",
    },
    {
        "id": "capability", "name": "capability-svc", "port": "8081", "color": "#7A5AF8",
        "title": "产研能力定义服务",
        "items": ["流程规范定义（任务类型/规范/工作流）",
                  "数字员工原型（原型/技能/运行配置）"],
        "db": "PostgreSQL（JSONB）+ Redis（缓存）",
        "fill": "#F5F3FF", "stroke": "#7A5AF8",
    },
    {
        "id": "iam", "name": "iam-svc", "port": "8082", "color": "#DC6803",
        "title": "用户权限服务",
        "items": ["用户/角色管理（类 EHR）", "RBAC 权限（菜单/按钮级）", "组织层级（部门+项目矩阵）"],
        "db": "PostgreSQL",
        "fill": "#FFF7ED", "stroke": "#DC6803",
    },
    {
        "id": "inf", "name": "inf-svc", "port": "8083", "color": "#027A48",
        "title": "基础设施服务",
        "items": ["实例生命周期", "Body 运行时", "WebSocket / ACP 协议", "AI 能力调用（模型路由+降级）"],
        "db": "PostgreSQL（JSONB）+ Redis（WS会话/锁/配额）",
        "fill": "#ECFDF3", "stroke": "#027A48",
    },
]

for i, svc in enumerate(svc_data):
    sx = bs_start_x + i * (bs_card_w + bs_gap)
    sy = bs_y

    # Card
    elements.append(make_rounded_rect(sid(f"{svc['id']}_card"), sx, sy, bs_card_w, bs_card_h,
                                       fill=svc["fill"], stroke=svc["stroke"], sw=1.5))

    # Service name + port
    elements.append(make_text(sid(f"{svc['id']}_name"), sx + 12, sy + 8, bs_card_w - 24, 26,
                              f"{svc['name']}", fs=15, color=svc["stroke"], bold=True))
    elements.append(make_text(sid(f"{svc['id']}_port"), sx + bs_card_w - 80, sy + 10, 68, 20,
                              f"端口 {svc['port']}", fs=11, color=TERTIARY_TEXT, align="right"))

    # Separator
    elements.append(make_line(sid(f"{svc['id']}_sep"), sx + 12, sy + 40, sx + bs_card_w - 12, sy + 40))

    # Role title
    elements.append(make_text(sid(f"{svc['id']}_role"), sx + 12, sy + 48, bs_card_w - 24, 20,
                              svc["title"], fs=12, color=svc["stroke"], bold=True))

    # Items
    item_y = sy + 72
    for j, item in enumerate(svc["items"]):
        elements.append(make_text(sid(f"{svc['id']}_item{j}"), sx + 20, item_y + j * 24,
                                  bs_card_w - 32, 22,
                                  f"• {item}", fs=12, color=SECONDARY_TEXT))

    # Database
    db_y = sy + bs_card_h - 60
    elements.append(make_line(sid(f"{svc['id']}_dbsep"), sx + 12, db_y - 8, sx + bs_card_w - 12, db_y - 8,
                               stroke=DIVIDER))
    elements.append(make_text(sid(f"{svc['id']}_db"), sx + 14, db_y, bs_card_w - 28, 22,
                              svc["db"], fs=11, color=TERTIARY_TEXT))

    if svc["id"] == "capability":
        # Note about merge reason
        elements.append(make_text(sid("cap_note"), sx + 14, db_y + 26, bs_card_w - 28, 24,
                                  "※ 流程改必牵扯改原型，合并避免分布式事务",
                                  fs=10, color=TERTIARY_TEXT))

# Service-to-service arrows (simplified)
# pdm → capability
elements.append(make_arrow(sid("ar_pdm_cap"), bs_start_x + bs_card_w, bs_y + bs_card_h//2,
                            [[0, 0], [bs_gap - 4, 0]],
                            stroke="#175CD3", sw=1.5))

# pdm → inf
pdm_rx = bs_start_x + bs_card_w
inf_lx = bs_start_x + 3 * (bs_card_w + bs_gap)
mid_x = (pdm_rx + inf_lx) // 2
elements.append(make_arrow(sid("ar_pdm_inf"), pdm_rx, bs_y + bs_card_h//2 + 20,
                            [[0, 0], [mid_x - pdm_rx, 0], [inf_lx - pdm_rx, bs_card_h//2 + 10]],
                            stroke=TERTIARY_TEXT, sw=1.5))

# capability → inf
elements.append(make_arrow(sid("ar_cap_inf"), bs_start_x + bs_card_w + bs_gap + bs_card_w,
                            bs_y + bs_card_h//2 + 30,
                            [[0, 0], [bs_gap + bs_card_w - 4, 0]],
                            stroke=TERTIARY_TEXT, sw=1.5))

# Legend inside service area
arrow_legend_y = bs_y + bs_card_h + 30
elements.append(make_text(sid("arrow_legend"), svr_x + 40, arrow_legend_y, 600, 22,
                          "── 实线 = OpenFeign / REST 同步调用    · · · 虚线 = RabbitMQ 异步事件（未画出，避免拥挤）",
                          fs=11, color=TERTIARY_TEXT))

# ── 2c: Infrastructure ──
infra_y = arrow_legend_y + 50
infra_card_w = 310
infra_card_h = 65
infra_gap = 40
infra_start_x = svr_x + 60

infra_data = [
    ("Nacos", "8848", "注册中心 + 配置中心", DATA_FILL, DATA_STROKE),
    ("RabbitMQ", "5672", "异步事件总线", DATA_FILL, DATA_STROKE),
    ("PostgreSQL 16+", "5432", "统一存储（单库多 Schema）", DATA_FILL, DATA_STROKE),
    ("Redis", "6379", "缓存 / 会话 / 限流 / 分布式锁", DATA_FILL, DATA_STROKE),
]

for i, (name, port, desc, fill, stroke) in enumerate(infra_data):
    ix = infra_start_x + i * (infra_card_w + infra_gap)
    iy = infra_y

    elements.append(make_rounded_rect(sid(f"infra{i}_box"), ix, iy, infra_card_w, infra_card_h,
                                       fill=fill, stroke=stroke, sw=1.5))
    elements.append(make_text(sid(f"infra{i}_title"), ix + 12, iy + 4, infra_card_w - 24, 22,
                              f"{name}", fs=14, color=stroke, bold=True))
    elements.append(make_text(sid(f"infra{i}_port"), ix + infra_card_w - 60, iy + 6, 48, 18,
                              f":{port}", fs=10, color=TERTIARY_TEXT, align="right"))
    elements.append(make_text(sid(f"infra{i}_desc"), ix + 12, iy + 30, infra_card_w - 24, 28,
                              desc, fs=12, color=SECONDARY_TEXT))

# Growth phase note
growth_y = infra_y + infra_card_h + 20
elements.append(make_text(sid("growth_note"), svr_x + 40, growth_y, svr_w - 80, 22,
                          "成长期新增：Kubernetes 编排  ·  Prometheus + Grafana 监控  ·  Jaeger 链路追踪  ·  独立 PG 分库  ·  向量数据库  |  成熟期新增：Istio 服务网格",
                          fs=11, color=TERTIARY_TEXT, align="center"))

# ============================================================
# CHANNEL 2 BAR (y: 1500 ~ 1540)
# ============================================================
ch2_y = svr_y + svr_h + 20
elements.append(make_rounded_rect(sid("ch2_bar"), 80, ch2_y, 1440, 40,
                                   fill="#F3E8FF", stroke="#9333EA", sw=1.5))
elements.append(make_text(sid("ch2_label"), 100, ch2_y + 2, 200, 36,
                          "通道 2：", fs=13, color="#9333EA", bold=True))
elements.append(make_text(sid("ch2_detail"), 210, ch2_y + 2, 1280, 36,
                          "WebSocket (wss://) 长连接  —  JSON-RPC 2.0  —  心跳保活  ·  断线重连  ·  sync.snapshot 对账  —  WS-Token 认证（60min + 7天 refresh）",
                          fs=12, color=SECONDARY_TEXT))

# ============================================================
# LAYER 3: ACP NODE & AGENTS (y: 1560 ~ 2020)
# ============================================================

acp_y = ch2_y + 70
acp_w = 1340
acp_h = 280
acp_x = svr_x + 50

elements.append(make_rounded_rect(sid("acp_box"), acp_x, acp_y, acp_w, acp_h,
                                   fill="#FAF5FF", stroke="#7A5AF8", sw=2))

elements.append(make_text(sid("acp_title"), acp_x + 20, acp_y + 8, 500, 30,
                          "数字员工节点（ACP 守护进程 — Rust）", fs=18, color=AI_STROKE, bold=True))

# ACP modules
mod_w = 280
mod_h = 56
mod_gap_x = 30
mod_gap_y = 20
mod_start_x = acp_x + 40
mod_start_y = acp_y + 55

acp_modules = [
    ("ConnectionMgr", "WS 连接管理（心跳/重连/Token 续期）"),
    ("MessageRouter", "双向消息路由"),
    ("DriverRegistry", "Driver 注册表"),
    ("ProtocolAdapter", "协议翻译（JSON-RPC ↔ Agent 原生）"),
    ("ProcessManager", "Agent 进程管理（spawn / 监控 / 停止）"),
    ("ConfigManager", "本地配置管理"),
    ("SecretManager", "密钥注入与释放"),
]

for j, (name, desc) in enumerate(acp_modules):
    if j < 4:
        mx = mod_start_x + j * (mod_w + mod_gap_x)
        my = mod_start_y
    else:
        mx = mod_start_x + (j - 4) * (mod_w + mod_gap_x) + 60
        my = mod_start_y + mod_h + mod_gap_y

    elements.append(make_rounded_rect(sid(f"acp_mod{j}"), mx, my, mod_w, mod_h,
                                       fill="#FFFFFF", stroke=AI_STROKE, sw=1))
    elements.append(make_text(sid(f"acp_mod{j}_name"), mx + 12, my + 4, mod_w - 24, 24,
                              name, fs=13, color=AI_STROKE, bold=True))
    elements.append(make_text(sid(f"acp_mod{j}_desc"), mx + 12, my + 28, mod_w - 24, 24,
                              desc, fs=10, color=SECONDARY_TEXT))

# Agent instances (below ACP)
agent_y = acp_y + acp_h + 40
agent_w = 390
agent_h = 65
agent_gap = 50
agent_start_x = acp_x + 40

agent_data = [
    ("Hermes", "自研 CLI Agent", "stdin / stdout 管道", "#7A5AF8"),
    ("Claude Code", "Anthropic CLI Agent", "stdin / stdout 管道", "#7A5AF8"),
    ("HTTP Agent 服务", "远程 Agent", "HTTP API + SSE", "#7A5AF8"),
]

for j, (name, stype, proto, color) in enumerate(agent_data):
    ax = agent_start_x + j * (agent_w + agent_gap)
    ay = agent_y

    elements.append(make_rounded_rect(sid(f"agent{j}"), ax, ay, agent_w, agent_h,
                                       fill="#FFFFFF", stroke=color, sw=1.5))
    elements.append(make_text(sid(f"agent{j}_name"), ax + 14, ay + 6, agent_w - 28, 24,
                              name, fs=14, color=color, bold=True))
    elements.append(make_text(sid(f"agent{j}_type"), ax + 14, ay + 30, agent_w - 28, 28,
                              f"{stype}  ·  {proto}", fs=11, color=SECONDARY_TEXT))

# Body note
body_y = agent_y + agent_h + 20
elements.append(make_text(sid("body_note"), agent_start_x, body_y, agent_w * 3 + agent_gap * 2, 24,
                          "数字员工节点 + Agent 进程 = Body（一个数字员工的运行态）",
                          fs=14, color=AI_STROKE, bold=True, align="center"))

# Down arrows from ACP to agents
for j in range(3):
    acp_module_cx = mod_start_x + (j % 4) * (mod_w + mod_gap_x) + mod_w // 2
    agent_cx = agent_start_x + j * (agent_w + agent_gap) + agent_w // 2
    elements.append(make_line(sid(f"down_arrow{j}"),
                              agent_cx, acp_y + acp_h + 6,
                              agent_cx, agent_y - 6,
                              stroke=AI_STROKE, sw=1.5))

# ============================================================
# EXTERNAL: LLM API
# ============================================================

# Arrow from inf-svc to LLM
llm_x = bs_start_x + 3 * (bs_card_w + bs_gap) + bs_card_w + 40
llm_y = bs_y + bs_card_h // 2 - 30
llm_box_x = llm_x + 40
llm_box_y = bs_y + bs_card_h // 4

elements.append(make_arrow(sid("ar_inf_llm"), bs_start_x + 3 * (bs_card_w + bs_gap) + bs_card_w,
                            llm_y,
                            [[0, 0], [llm_box_x - (bs_start_x + 3*(bs_card_w+bs_gap)+bs_card_w), 0]],
                            stroke=EXT_STROKE, sw=1.5))

# LLM API box
elements.append(make_rounded_rect(sid("llm_box"), llm_box_x, llm_box_y, 200, 70,
                                   fill=EXT_FILL, stroke=EXT_STROKE, sw=1.5))
elements.append(make_text(sid("llm_title"), llm_box_x + 10, llm_box_y + 6, 180, 24,
                          "LLM API 提供商", fs=13, color=EXT_STROKE, bold=True))
elements.append(make_text(sid("llm_desc"), llm_box_x + 10, llm_box_y + 32, 180, 30,
                          "OpenAI / Claude / 其他\n模型路由 + 降级切换", fs=10, color=SECONDARY_TEXT))

# ============================================================
# LEGEND
# ============================================================
leg_x = 80
leg_y = body_y + 44
leg_w = 1440
leg_h = 95

elements.append(make_rounded_rect(sid("legend_box"), leg_x, leg_y, leg_w, leg_h,
                                   fill="#F9FAFB", stroke=DIVIDER, sw=1))

legend_items = [
    ("实线箭头 →", "同步调用（OpenFeign / REST）", NEUTRAL_STROKE),
    ("虚线箭头 ⇢", "异步事件（RabbitMQ）", TERTIARY_TEXT),
    ("双向粗线 ⇄", "WebSocket 长连接", "#9333EA"),
    ("单向细线 →", "SSE 推送", DATA_STROKE),
    ("虚线框", "成长期引入", DIVIDER),
]
for j, (symbol, meaning, color) in enumerate(legend_items):
    lx = leg_x + 30 + j * 260
    elements.append(make_text(sid(f"leg{j}_sym"), lx, leg_y + 8, 80, 24,
                              symbol, fs=12, color=color, bold=True))
    elements.append(make_text(sid(f"leg{j}_mean"), lx + 90, leg_y + 8, 150, 24,
                              meaning, fs=12, color=SECONDARY_TEXT))

# Legend second row: color semantics
leg_row2_y = leg_y + 50
elements.append(make_text(sid("leg_purple"), leg_x + 30, leg_row2_y, 260, 24,
                          "🟣 紫色 = 数字员工 / AI", fs=11, color=AI_STROKE))
elements.append(make_text(sid("leg_blue"), leg_x + 300, leg_row2_y, 260, 24,
                          "🔵 蓝色 = 数据 / 存储 / 网关", fs=11, color=DATA_STROKE))
elements.append(make_text(sid("leg_green"), leg_x + 560, leg_row2_y, 260, 24,
                          "🟢 绿色 = 基础设施 / inf-svc", fs=11, color="#027A48"))
elements.append(make_text(sid("leg_orange"), leg_x + 810, leg_row2_y, 260, 24,
                          "🟠 橙色 = 用户权限 / 配置", fs=11, color="#DC6803"))
elements.append(make_text(sid("leg_purple_ext"), leg_x + 1060, leg_row2_y, 260, 24,
                          "🟣 深紫 = 外部系统", fs=11, color=EXT_STROKE))

# ============================================================
# BUILD FILE
# ============================================================

excalidraw = {
    "type": "excalidraw",
    "version": 2,
    "source": "https://excalidraw.com",
    "elements": elements,
    "appState": {
        "viewBackgroundColor": "#FFFFFF",
        "gridSize": 20
    },
    "files": {}
}

output_path = "/Users/jinmo/workspace/LegionOS/docs/architecture/diagrams/panoramic-architecture.excalidraw"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(excalidraw, f, ensure_ascii=False, indent=2)

print(f"✅ Generated: {output_path}")
print(f"   Total elements: {len(elements)}")
