---
name: law086
description: 案件云(law086) AI集成。让律师通过自然语言操作案件云：查询案件列表和详情、更新案件进度和状态、管理日程、查看和更新客户信息、查看项目信息、查看财务记录和应收款、查看和更新工作记录、生成文书模板。当用户说"查询案件"、"我的案件"、"更新案件状态"、"查看日程"、"创建日程"、"查看财务"、"案件云"、"帮我查案件"、"今天有什么安排"、"帮我记录"、"查看客户"、"更新客户"、"查看项目"、"团队日程"、"应收款"、"更新记录"、"标记已办"时触发此技能。
---

# 案件云 Open API 集成 V2.0

通过 PAT (Personal Access Token) 授权，用自然语言操作案件云系统。

## 前置配置

### 1. 获取 PAT Token

指导用户在案件云中生成 PAT：
1. 登录案件云 OA (https://oa.law086.com)
2. 进入 **个人设置 > AI管理**
3. 点击"生成新令牌"
4. 填写名称、选择过期时间和权限范围
5. 复制生成的 Token（以 `law086_pat_` 开头）

### 2. 配置系统访问地址和 PAT Token

`.env` 文件（与 SKILL.md 同级）中存放 `API_BASE_URL` 和 `PAT_TOKEN`。

若 `PAT_TOKEN` 为默认占位值（如 `law086_pat_xxx...`），提示用户替换为自己的 Token。

## API 调用方式

### 使用 api.py 脚本（推荐）

所有 API 调用统一通过 `scripts/api.py` 脚本发送，脚本自动处理认证、编码和响应解析：

```bash
python3 .claude/skills/law086/scripts/api.py <METHOD> <PATH> [JSON_BODY]
```

**示例**：
```bash
# GET 请求
python3 .claude/skills/law086/scripts/api.py GET /cases
python3 .claude/skills/law086/scripts/api.py GET "/cases?keyword=张三&g_status=1"
python3 .claude/skills/law086/scripts/api.py GET /dashboard

# POST 请求（中文 body 直接写，无需担心编码）
python3 .claude/skills/law086/scripts/api.py POST /calendar '{"title":"开庭","htime":"2026-05-10 14:00","endtime":"2026-05-10 15:00"}'

# PATCH 请求
python3 .claude/skills/law086/scripts/api.py PATCH /cases/ABC123 '{"stage_text":"已开庭"}'
python3 .claude/skills/law086/scripts/api.py PATCH /records/xyz789 '{"hstatus":1}'
```

**脚本特性**：
- 自动从 `.env` 加载 `API_BASE_URL` 和 `PAT_TOKEN`
- 自动处理 URL 中的中文编码
- 自动处理 POST/PATCH body 的 UTF-8 编码
- 统一 JSON 响应输出
- Token 过期、权限不足等错误自动提示

### 响应格式

```json
{"code": "0", "msg": "", "data": {...}}
```
- 成功: `code == "0"` (宽松比较，兼容整数 0 和字符串 "0")
- 认证失败: `code == "2"`
- 权限不足: `code == "3"`
- 业务错误: `code == "1"`

### 时区

系统使用**中国标准时间 (CST, UTC+8)**。所有日期判断（今天、本周、本月）均按北京时间计算。在生成日期参数时，请确保使用北京时间（而非 UTC）。

例如：当 UTC 时间为 `2026-04-27 00:00` 时，北京时间已是 `2026-04-27 08:00`，应视为 4 月 27 日。

### 错误处理

| code | 含义 | 处理方式 |
|------|------|----------|
| "2" | Token 无效或已过期 | 提示用户重新生成 PAT |
| "3" | 权限不足 | 提示用户重新生成 PAT 并勾选对应权限 |
| "1" | 业务错误 | 展示 msg 中的错误信息 |

## 端点说明

详细 API 文档见 [references/api-reference.md](references/api-reference.md)。

### 每日概览 (dashboard.read)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /dashboard | 每日概览（今日日程、案件动态、待办提醒等） |

### 案件 (cases.read / cases.write)

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| GET | /cases | cases.read | 案件列表。支持 `keyword`(搜索)、`g_status`(1=在办/2=结案/3=归档)、`type`(1=民事/2=商事/3=仲裁/4=刑事/5=行政) 筛选 |
| GET | /cases/{code} | cases.read | 案件详情（含当事人、办理人员、阶段、受理单位、财务概览）。{code}=case_code |
| PATCH | /cases/{code} | cases.write | 丰富案件更新。支持: `process_code`(审理程序)、`case_mark`(标记)、`anhao`(案号)、`degree`(紧急程度)、`current_stage_id`(当前阶段) |
| GET | /cases/{code}/stages | cases.read | 案件阶段列表（含各阶段下的办案记录） |
| GET | /cases/{code}/records | cases.read | 案件办案记录列表 |
| POST | /cases/{code}/records | cases.write | 添加办案记录（自动同步为日程）。需 `title`、`content`、`stage_id` 等 |

### 日程 (calendar.read / calendar.write)

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| GET | /team/members | calendar.read | 团队成员列表（返回 uid 和姓名，uid 为 hashid 编码）。个人空间下不可用 |
| GET | /calendar | calendar.read | 日程列表。使用 `start_date`/`end_date` 过滤（格式 YYYY-MM-DD）；`is_team=1` 查看团队日程（团队版以上）；`uids` 指定团队成员（用 `/team/members` 返回的 hashid，逗号分隔） |
| POST | /calendar | calendar.write | 创建日程。需 `title`、`htime`、`endtime`；可选 `content`、`linkid`+`type` 关联案件/项目、`time_cost` 时间花费（分钟） |
| PUT | /calendar/{id} | calendar.write | 更新日程。支持 `title`、`content`、`htime`、`endtime`、`hstatus`、`time_cost` |

### 客户 (clients.read / clients.write)

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| GET | /clients | clients.read | 客户列表。支持 `keyword` 搜索 |
| GET | /clients/{code} | clients.read | 客户详情（含关联案件列表）。{code}=客户编码 |
| PATCH | /clients/{code} | clients.write | 更新客户信息。支持: `name`、`mark`(1=单位/2=个人)、`type`(1=签约/2=意向/3=潜在/4=终止)、`degree`(1=次要/2=一般/3=重要/4=核心)、`address`、`description`、`contact`、`card_num` 等 |
| GET | /clients/{code}/contacts | clients.read | 客户联系人列表 |

### 记录 (records.read / records.write)

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| GET | /records/{id} | records.read | 记录详情（通过记录 hashid 直接获取，无需知道所属案件/项目） |
| PATCH | /records/{id} | records.write | 更新记录。支持: `title`、`content`、`hstatus`(0=待办/1=已办)、`htime`、`endtime`、`time_cost`(分钟)、`stage` |

### 项目 (projects.read / projects.write)

| 方法 | 路径 | Scope | 说明 |
|------|------|-------|------|
| GET | /projects | projects.read | 项目列表。支持 `keyword`(搜索项目名称/编号)、`pr_status`(1=进行中/2=已结束)、`pr_type`(项目类型)、`degree`(0=次要/1=一般/2=重要) 筛选 |
| GET | /projects/{code} | projects.read | 项目详情（含项目团队、关联客户及联系人）。{code}=pr_code |
| PATCH | /projects/{code} | projects.write | 更新项目信息。支持: `pr_name`、`pr_status`、`stage_text`、`degree`、`funding` 等 |

### 财务 (finance.read) — 高阶版以上

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /finance | 财务记录列表。支持分页 |
| GET | /finance/{id} | 单条财务记录详情 |
| GET | /finance/receivables | 应收款列表 |
| GET | /finance/receivables/{id} | 应收款详情 |
| GET | /finance/summary | 财务摘要（收支统计） |

> 财务功能需要用户订阅高阶版以上套餐，否则返回权限不足。

### 搜索 (cases.read)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /search | 统一搜索（跨案件+客户+项目）。参数 `keyword` |

### 枚举 (无权限要求)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /enums | 获取所有枚举映射（案件类型、状态、审理程序、紧急程度等） |

## 关键概念

### 办案记录 vs 日程

- **办案记录** (`POST /cases/{code}/records`) 是案件阶段下的工作日志，添加后会**自动同步为日程**。
- 要创建不关联案件的一般日程，使用 `POST /calendar`。

### 日程查询的时间范围

**重要**: 不要使用 `today=1` 或 `this_week=1` 参数（服务端过滤不精确）。应始终用 `start_date`/`end_date` 传入具体日期：

- **今天**: `start_date=今天日期&end_date=今天日期`
- **本周**: `start_date=本周周一&end_date=本周周日`（周一为一周起始）
- **本月**: `start_date=本月1号&end_date=本月最后一天`
- 用户未明确指定时间范围时，默认查询**本周**

### 团队日程

- `is_team=1` 查看团队所有成员日程（需团队版以上）。
- 用 `GET /team/members` 获取团队成员列表（返回 hashid 编码的 uid 和姓名）。
- `uids=hashid1,hashid2` 指定查看特定成员的日程（值来自 `/team/members` 返回的 uid 字段）。
- 展示团队日程时，按日期分组、按 `htime` 时间升序排列，优先展示 `huser_text`（负责人姓名）和 `type_text`（关联类型）。
- 日程列表已返回 `htime_text`、`huser_text`、`assit_text`、`type_text`、`case_name` 等文本字段，直接使用即可，无需手动转换。

### 版本限制

- **财务功能**: 需高阶版以上套餐。
- **团队日程**: 需团队版以上套餐。

## 高危操作

以下操作在执行前**必须**向用户确认（展示操作摘要，询问"确认执行？"，用户明确同意后才发送请求）：

- **PATCH /cases/{code}** 中变更 `process_code`（审理程序变更影响案件流程）

## 使用示例

| 用户说 | 推断意图 | 脚本调用 |
|--------|----------|----------|
| "查询我的案件" | 案件列表 | `api.py GET /cases` |
| "张三案件进度" | 搜索案件 | `api.py GET "/cases?keyword=张三"` |
| "在办案件" | 筛选状态 | `api.py GET "/cases?g_status=1"` |
| "案件ABC123详情" | 案件详情 | `api.py GET /cases/ABC123` |
| "案件ABC123的办案记录" | 办案记录 | `api.py GET /cases/ABC123/records` |
| "帮我记录：今天去法院阅卷" | 添加办案记录 | `api.py POST /cases/{code}/records '{"title":"去法院阅卷",...}'` |
| "把案件ABC123状态改为已开庭" | 更新案件 | **确认后** `api.py PATCH /cases/ABC123 '{"stage_text":"已开庭"}'` |
| "今天有什么安排" | 今日日程 | `api.py GET "/calendar?start_date=2026-05-06&end_date=2026-05-06"` |
| "创建一个明天下午2点的日程" | 创建日程 | `api.py POST /calendar '{"title":"...","htime":"2026-05-07 14:00","endtime":"2026-05-07 15:00"}'` |
| "团队日程" | 团队视图 | `api.py GET "/calendar?is_team=1&start_date=...&end_date=..."` |
| "查看客户张三" | 搜索客户 | `api.py GET "/clients?keyword=张三"` |
| "更新客户类型为签约" | 更新客户 | `api.py PATCH /clients/{code} '{"type":1}'` |
| "把记录标记为已办" | 更新记录 | `api.py PATCH /records/{id} '{"hstatus":1}'` |
| "查看我的项目" | 项目列表 | `api.py GET /projects` |
| "查看财务记录" | 财务列表 | `api.py GET /finance` |
| "案件云" | 每日概览 | `api.py GET /dashboard` |
