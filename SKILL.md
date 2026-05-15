---
name: law086
description: 案件云(law086) AI集成。让律师通过自然语言操作案件云：查询案件列表和详情、更新案件进度和状态、管理日程、查看和更新客户信息、创建客户、查看项目信息、创建项目、查看财务记录和应收款、查看和更新工作记录、生成文书模板。当用户说"查询案件"、"我的案件"、"更新案件状态"、"查看日程"、"创建日程"、"查看财务"、"案件云"、"帮我查案件"、"今天有什么安排"、"帮我记录"、"查看客户"、"更新客户"、"创建客户"、"新增客户"、"查看项目"、"创建项目"、"新增项目"、"团队日程"、"应收款"、"更新记录"、"标记已办"时触发此技能。
---

# 案件云 Open API 集成 V2.0

通过 PAT Token 授权，用自然语言操作案件云。详细 API 文档见 [references/api-reference.md](references/api-reference.md)。

## 前置配置

1. 用户在 OA「个人设置 > AI管理」生成 PAT Token（以 `law086_pat_` 开头）
2. 将 `API_BASE_URL` 和 `PAT_TOKEN` 写入 `.env` 文件（与 SKILL.md 同级）
3. 若 Token 为占位值，提示用户替换

## API 调用

```bash
python3 scripts/api.py <METHOD> <PATH> [JSON_BODY]
# 示例：
python3 scripts/api.py GET "/cases?keyword=张三&g_status=1"
python3 scripts/api.py POST /calendar '{"title":"开庭","htime":"2026-05-10 14:00","endtime":"2026-05-10 15:00","type":0}'
```

脚本自动处理认证、中文编码和响应解析。所有时间使用**北京时间 (CST, UTC+8)**。

### 响应与错误处理

| code | 含义 | 处理 |
|------|------|------|
| 0 | 成功 | 读取 data。**注意**: code 为整数，须用 `==` 宽松比较，禁止 `===` |
| 1 | 业务错误 | 展示 msg |
| 2 | Token 无效/过期 | 提示重新生成 PAT |
| 3 | 权限不足 | 提示重新生成 PAT 并勾选对应 scope |

## 端点速查

> 参数和响应字段的详细说明见 [references/api-reference.md](references/api-reference.md)。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /dashboard | 每日概览（今日日程、案件动态、待办） |
| GET | /search?keyword= | 统一搜索（跨案件+客户+项目） |
| GET | /enums | 枚举数据字典（案件类型、状态等） |
| GET | /cases | 案件列表（keyword/g_status/type 筛选） |
| GET | /cases/{code} | 案件详情（含当事人、阶段、财务） |
| PATCH | /cases/{code} | 更新案件（stage_text/degree/anhao 等）⚠️ process_code 需确认 |
| GET | /cases/{code}/stages | 案件阶段列表 |
| GET | /cases/{code}/records | 案件办案记录（仅查询） |
| GET | /calendar | 日程列表（用 start_date/end_date，禁用 today/this_week） |
| POST | /calendar | 创建日程（必填: title/htime/endtime/type） |
| PUT | /calendar/{id} | 更新日程 |
| GET | /team/members | 团队成员列表（个人空间不可用） |
| GET | /clients | 客户列表（keyword 搜索） |
| GET | /clients/{code} | 客户详情（含关联案件） |
| GET | /clients/create-form | 获取客户创建表单 schema |
| POST | /clients | 创建客户 |
| PATCH | /clients/{code} | 更新客户 |
| GET | /clients/{code}/contacts | 客户联系人 |
| GET | /projects | 项目列表 |
| GET | /projects/{code} | 项目详情（含团队、关联客户） |
| GET | /projects/create-form | 获取项目创建表单 schema |
| POST | /projects | 创建项目 |
| PATCH | /projects/{code} | 更新项目 |
| GET | /finance | 财务记录（高阶版以上） |
| GET | /finance/receivables | 应收款列表 |
| GET | /finance/summary | 财务摘要 |
| GET | /records/{id} | 记录详情 |
| PATCH | /records/{id} | 更新记录（hstatus/time_cost 等） |

## 关键概念

### 日程与办案记录的关系

日程和办案记录是同一张表的不同视图。`POST /calendar` 是创建日程/待办/提醒的唯一入口。`GET /cases/{code}/records` 仅用于查询某案件的办理历史。

### 日程关联（重要）

创建日程时**必须主动识别用户语境中的关联实体**，通过 `linkid`+`type` 建立关联。`type` 为必填字段。

**规则：只要用户提到具体的案件、项目或客户名称，就必须先搜索获取其 `id`，然后在创建日程时传入 `linkid` 和对应的 `type`。禁止在已识别到实体的情况下传 `type:0`。**

| type | 含义 | linkid 来源 |
|------|------|-------------|
| 0 | 不关联 | 无（仅在用户完全没提到任何实体时使用） |
| 1 | 案件 | `GET /cases` 返回的 `id`（hashid 字符串） |
| 2 | 项目 | `GET /projects` 返回的 `id`（hashid 字符串） |
| 3 | 客户 | `GET /clients` 返回的 `id`（hashid 字符串） |

识别优先级：案件(1) > 项目(2) > 客户(3)。`linkid` 直接使用实体返回的 `id` 字段值（hashid 字符串，如 `"J3GGbB3j"`），不要转成 int。

**示例**：用户说"江西建工案明天开庭"→ 搜索案件 → `POST /calendar '{"title":"开庭","htime":"...","endtime":"...","type":1,"linkid":"B31ewk3n"}'`

### time_cost vs htime/endtime

- **`htime`/`endtime`** = 日程起止时间（什么时候开会）
- **`time_cost`** = 实际工时（分钟），用于统计。"花费了2.5小时"→ `time_cost=150`，不是改 endtime

### 日程查询时间范围

始终用 `start_date`/`end_date`（YYYY-MM-DD），**禁用** `today`/`this_week`（服务端不准）。默认查本周。

### 团队日程

`is_team=1` 查看团队日程（需团队版以上），`uids` 用 `/team/members` 返回的 hashid。展示用 `htime_text`/`huser_text`/`type_text` 等后端预处理好字段。

### 创建流程（客户/项目）

创建客户或项目前，**必须先调 `create-form` 端点**获取完整表单 schema（含枚举选项、级联树、自定义字段等）。流程：

1. AI 调用 `GET /clients/create-form` 或 `GET /projects/create-form` 获取表单 schema
2. AI 根据 schema 将用户描述映射为正确的枚举值和分类 ID
3. AI 展示确认信息（人类可读格式），等待用户确认
4. 用户确认后，AI 调用 `POST /clients` 或 `POST /projects` 创建
5. 创建成功后返回实体编号（客户返回 `code`/`c_num`，项目返回 `pr_code`/`p_num`）

**关键**：schema 中的枚举选项和级联树由后端动态返回，AI 必须依据 schema 中的值进行映射，不能凭猜测。

## 高危操作

- **PATCH /cases/{code}** 中变更 `process_code`（审理程序变更影响流程）→ 必须先确认

## 使用示例

| 用户说 | 推断意图 | 脚本调用 |
|--------|----------|----------|
| "查询我的案件" | 案件列表 | `GET /cases` |
| "张三案件进度" | 搜索案件 | `GET "/cases?keyword=张三"` |
| "在办案件" | 筛选状态 | `GET "/cases?g_status=1"` |
| "案件ABC123详情" | 案件详情 | `GET /cases/ABC123` |
| "帮我记录：去法院阅卷" | 添加办案记录 | `POST /calendar '{title,htime,endtime,type:1,linkid:case_id}'` |
| "今天有什么安排" | 今日日程 | `GET "/calendar?start_date=今天&end_date=今天"` |
| "创建明天下午2点的日程" | 创建日程 | `POST /calendar '{title,htime,endtime,type:0}'` |
| "明天约小康米开会" | 关联客户日程 | 先 `GET "/clients?keyword=小康米"` → `POST /calendar '{...,linkid:id,type:3}'` |
| "帮小米案加开庭日程" | 关联案件日程 | 先 `GET "/cases?keyword=小米"` → `POST /calendar '{...,linkid:id,type:1}'` |
| "日程花费了2.5小时" | 记录工时 | `PUT /calendar/{id} '{"time_cost":150}'` |
| "把记录标记为已办" | 更新记录 | `PATCH /records/{id} '{"hstatus":1}'` |
| "更新客户类型为签约" | 更新客户 | `PATCH /clients/{code} '{"type":1}'` |
| "帮我创建客户张三，个人，电话138xxxx" | 创建客户 | `GET /clients/create-form` → 确认 → `POST /clients '{name,mark,contact,...}'` |
| "创建一个单位客户华为" | 创建客户 | `GET /clients/create-form` → 确认 → `POST /clients '{name:"华为",mark:1,...}'` |
| "新建一个项目xxx，合同纠纷，预算5万" | 创建项目 | `GET /projects/create-form` → 确认 → `POST /projects '{pr_name,pr_type,pr_status,funding,...}'` |
| "团队日程" | 团队视图 | `GET "/calendar?is_team=1&start_date=...&end_date=..."` |
| "案件云" | 每日概览 | `GET /dashboard` |
