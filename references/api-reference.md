# 案件云 Open API 参考 (V2.0)

## 目录

- [认证与通用规范](#认证与通用规范)
- [Dashboard](#dashboard)
- [Cases 案件](#cases-案件)
- [Calendar 日程](#calendar-日程)
- [Clients 客户](#clients-客户)
- [Records 记录](#records-记录)
- [Projects 项目](#projects-项目)
- [Finance 财务](#finance-财务)
- [Search & Enums 搜索与枚举](#search--enums-搜索与枚举)
- [V1 兼容说明](#v1-兼容说明)
- [Scope 权限对照表](#scope-权限对照表)

---

## 认证与通用规范

### 请求认证

所有请求在 Header 中携带 PAT Token：

```
Authorization: Bearer {PAT_TOKEN}
```

Token 以 `law086_pat_` 开头，在 OA「个人设置 > AI管理」中生成。

### Base URL

从环境配置读取 `API_BASE_URL`，例如 `https://open.law086.com/api/v1`

### 响应格式

```json
{"code": 0, "msg": "", "data": {...}}
```

| code | 含义 | 处理方式 |
|------|------|----------|
| 0 | 成功 | 读取 data |
| 1 | 业务错误 | 展示 msg |
| 2 | 认证失败 | 提示重新生成 PAT |
| 3 | 权限不足 | 提示重新勾选 scope |

> **重要**: code 为**整数**，前端须用 `==` 宽松比较：`res.code == "0"`。禁止 `===` 严格比较。

### 请求编码

POST/PUT 请求体含中文时，须先写入临时文件再用 `curl -d @file` 发送（避免 Windows GBK 编码问题）。

```bash
echo '{"title":"开庭","htime":"2026-04-15 14:00:00"}' > /tmp/open_req.json
curl -s -X POST "{BASE}/calendar" -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json" -d @/tmp/open_req.json
```

### 分页约定

分页接口返回标准 Laravel 分页结构：

| 字段 | 说明 |
|------|------|
| data | 数据列表 |
| current_page | 当前页码 |
| per_page | 每页条数 |
| total | 总条数 |
| last_page | 末页页码 |

---

## Dashboard

### GET /dashboard - 每日概览

Scope: `dashboard.read`

返回当前用户当日的待办事项、日程、案件统计等摘要信息。

**参数**: 无

**响应 data 字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| todo_count | int | 待办事项数 |
| today_records | array | 今日日程列表 |
| case_stats | object | 案件统计（在办/结案/归档数量） |
| unread_count | int | 未读消息数 |

> 注: 具体字段以实际返回为准，该端点为汇总视图。

---

## Cases 案件

### GET /cases - 案件列表

Scope: `cases.read`

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 否 | 按案件名称搜索 |
| g_status | int | 否 | 案件状态: 1=在办, 2=结案, 3=归档 |
| type | int | 否 | 案件类型: 1=民事, 2=商事, 3=仲裁, 4=刑事, 5=行政 |
| page | int | 否 | 页码，默认 1 |
| limit | int | 否 | 每页条数，默认 20 |

**响应 data 字段** (列表项):

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 案件 ID |
| case_name | string | 案件名称 |
| case_code | string | 案件编号 |
| c_num | string | 内部案号 |
| g_status | int | 状态 (1=在办, 2=结案, 3=归档) |
| type | int | 类型 (1=民事, 2=商事, 3=仲裁, 4=刑事, 5=行政) |
| org_id | int | 组织 ID |
| pr_time | string | 立案日期 |
| stage_text | string | 当前阶段文本 |
| degree | int | 等级 (0=次要, 1=一般, 2=重要) |
| created_at | string | 创建时间 |

### GET /cases/{id} - 案件详情

Scope: `cases.read`

返回完整案件信息，包含当事人、阶段、受理单位等。

**参数**: 路径参数 `id` (必填)

**响应 data 字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 案件 ID |
| case_name | string | 案件名称 |
| case_code | string | 案件编号 |
| c_num | string | 内部案号 |
| type | int | 案件类型 |
| g_status | int | 案件状态 |
| anyou | string | 案由 |
| stage_text | string | 当前阶段 |
| pr_time | string | 立案日期 |
| j_time | string | 结案日期 |
| g_time | string | 归档日期 |
| c_amount | decimal | 标的额 |
| w_fee | decimal | 代理费 |
| charge_desc | string | 收费说明 |
| case_mark | string | 案件备注 |
| unit_name | string | 受理单位名称 |
| unit_type | int | 受理单位类型 (1=法院, 2=检察院, 3=公安机关, 4=仲裁机构, 5=调解机构, 6=鉴定机构, 7=行政机构) |
| org_id | int | 组织 ID |
| degree | int | 等级 |
| fee_type | int | 收费类型 (1=定额, 2=风险, 3=计时, 4=计件, 5=免费) |
| process | string | 案件程序 |
| anhao | string | 案号 |
| privyc | array | 当事人列表 |
| privyc[].type | int | 1=委托方(原告), 2=对方(被告) |
| privyc[].name | string | 名称 |
| privyc[].c_type | int | 当事人细类 |
| privyc[].dsr_type | int | 1=个人, 2=单位 |
| privyc[].card_num | string | 证件号码 |
| privyc[].phone | string | 联系电话 |
| privyc[].address | string | 地址 |
| cl_id | int | 关联客户 ID |
| link_pr | int | 关联项目 ID |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

### PATCH /cases/{id} - 更新案件

Scope: `cases.write` | **高危操作，需二次确认**

V2 将 V1 的 PUT 改为 PATCH，支持更多可更新字段。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 案件状态文本 |
| g_status | int | 否 | 全局状态: 1=在办, 2=结案, 3=归档 |
| stage_text | string | 否 | 当前阶段文本 |
| case_mark | string | 否 | 案件备注（允许清空） |
| degree | int | 否 | 等级: 0=次要, 1=一般, 2=重要（只允许这三个值） |
| fee_type | int | 否 | 收费类型 |
| anyou | string | 否 | 案由 |
| unit_name | string | 否 | 受理单位名称 |
| unit_type | int | 否 | 受理单位类型 |
| process_code | int | 否 | 审理程序代码（只允许 GET /enums 返回的合法值） |
| anhao | string | 否 | 案号（最大 200 字） |
| charge_desc | string | 否 | 收费描述（最大 2000 字，允许清空） |
| current_stage_id | string | 否 | 当前阶段 ID（hashid，必须属于当前案件） |

> 至少提供一个字段。更新前须向用户展示变更摘要并确认。

**响应**: 返回更新后的案件完整数据。

### GET /cases/{id}/stages - 案件阶段列表

Scope: `cases.read`

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | int | 是 | 路径参数，案件 ID |

**响应 data 字段** (列表项):

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 阶段 ID |
| cid | int | 案件 ID |
| name | string | 阶段名称 |
| type | int | 类型 |
| active | int | 是否当前阶段 (1=是) |
| index | int | 排序序号 |

### GET /cases/{id}/records - 案件办案记录列表

Scope: `cases.read`

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | int | 是 | 路径参数，案件 ID |
| hstatus | int | 否 | 办理状态: 0=待办, 1=已办 |
| page | int | 否 | 页码 |
| limit | int | 否 | 每页条数 |

**响应 data 字段** (列表项):

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 记录 ID |
| rcode | string | 记录编码 |
| title | string | 标题 |
| content | string | 内容详情 |
| htime | int/string | 办理时间（时间戳或格式化时间） |
| endtime | int/string | 结束时间 |
| hstatus | int | 状态: 0=待办, 1=已办 |
| huser | int | 主办人 UID |
| assit | string | 协办人 UID 列表 |
| type | int | 关联类型: 1=案件 |
| linkid | int | 关联案件 ID |
| time_cost | int | 时间花费（分钟） |
| fee_cost | int | 费用花费 |
| stage | int | 所属阶段 ID |
| rtype | string | 工作摘要/分类 |

### POST /cases/{id}/records - 添加办案记录

Scope: `cases.write`

添加办案记录的同时会同步创建一条日程。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | int | 是 | 路径参数，案件 ID |
| title | string | 是 | 记录标题 |
| content | string | 否 | 记录内容 |
| htime | string | 是 | 办理时间 (YYYY-MM-DD HH:mm) |
| endtime | string | 否 | 结束时间 (YYYY-MM-DD HH:mm) |
| hstatus | int | 否 | 办理状态: 0=待办(默认), 1=已办 |
| rtype | string | 否 | 工作摘要 |
| time_cost | int | 否 | 时间花费（分钟） |
| fee_cost | int | 否 | 费用花费 |
| stage | int | 否 | 阶段 ID |

> 该操作会同时创建一条日程（type=1, linkid=案件ID），实现记录与日程同步。

**响应**: 返回创建的记录数据。

---

## Calendar 日程

### GET /team/members - 团队成员列表

Scope: `calendar.read`

返回当前组织下所有有效成员。**个人空间下不可用**（返回错误）。

**参数**: 无

**响应 data 字段** (列表项):

| 字段 | 类型 | 说明 |
|------|------|------|
| uid | string | 成员 UID（hashid 编码，用于 `GET /calendar?uids=` 参数） |
| real_name | string | 成员姓名 |

**响应示例**:
```json
{
  "code": 0,
  "data": [
    {"uid": "aB3xKp", "real_name": "张三"},
    {"uid": "mN9wRq", "real_name": "李四"}
  ]
}
```

### GET /calendar - 日程列表

Scope: `calendar.read`

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_date | string | 否 | 开始日期 (YYYY-MM-DD) |
| end_date | string | 否 | 结束日期 (YYYY-MM-DD) |
| is_team | int | 否 | 团队视图: 0=个人(默认), 1=团队 |
| uids | string | 否 | 指定团队成员，逗号分隔的 hashid（来自 `GET /team/members` 返回的 uid 字段，如 `aB3xKp,mN9wRq`） |
| hstatus | int | 否 | 状态: 0=待办, 1=已办 |
| limit | int | 否 | 每页条数，默认 20 |

> **注意**: 不要使用 `today=1` 或 `this_week=1` 快捷参数，服务端过滤不精确。应始终用 `start_date`/`end_date` 传入具体日期范围。

**响应 data 字段** (列表项):

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 日程 ID（hashid 编码） |
| rcode | string | 日程编码 |
| title | string | 日程标题 |
| content | string | 日程内容 |
| htime | int | 开始时间戳 |
| endtime | int | 结束时间戳（0 表示无结束时间） |
| htime_text | string | 开始时间文本（YYYY-MM-DD HH:mm） |
| endtime_text | string | 结束时间文本 |
| huser | string | 主办人 UID（hashid 编码） |
| huser_text | string | 主办人姓名 |
| assit | string | 协办人 UID 列表（hashid 编码，逗号分隔） |
| assit_text | string | 协办人姓名（逗号分隔） |
| type | int | 关联类型: 0=不关联, 1=案件, 2=项目, 3=客户 |
| type_text | string | 关联类型文本：不关联/案件/项目/客户 |
| linkid | string | 关联资源 ID（hashid 编码） |
| hstatus | int | 状态: 0=待办, 1=已办 |
| hstatus_text | string | 状态文本：待办/已办 |
| time_cost | int | 时间花费（小时，保留1位小数） |
| time_cost_text | string | 时间花费可读格式，如 "1.5小时"、"0小时" |
| case_name | string | 关联案件名称（仅 type=1 时有值） |
| allday | int | 是否全天: 0=否, 1=是 |
| remind_time | string | 提醒时间 |
| repeat_rule | string/json | 重复规则 |
| is_private | int | 是否私密: 0=否, 1=是 |
| add_uid | string | 创建人 UID（hashid 编码） |
| stage | string | 阶段 ID（hashid 编码，0 表示无阶段） |
| created_at | string | 创建时间 |

> **展示建议**: 优先使用 `htime_text`/`endtime_text` 显示时间，`huser_text`/`assit_text` 显示负责人，`type_text`+`case_name` 显示关联信息。这些字段已由后端处理好，无需二次转换。

### POST /calendar - 创建日程

Scope: `calendar.write`

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 日程标题（最大 200 字符，不可为空） |
| htime | string | 是 | 开始时间 (YYYY-MM-DD HH:mm) |
| endtime | string | 是 | 结束时间 (YYYY-MM-DD HH:mm)，必须 >= htime |
| content | string | 否 | 日程内容 |
| linkid | int | 否 | 关联案件/项目/客户 ID |
| type | int | 否 | 关联类型: 0=不关联, 1=案件, 2=项目, 3=客户（只允许这四个值） |
| rtype | string | 否 | 工作摘要/分类 |
| time_cost | int | 否 | 时间花费（分钟），必须 >= 0 |
| allday | int | 否 | 是否全天: 0=否, 1=是 |
| remind_time | string | 否 | 提醒时间 |

**响应**: 返回创建的日程数据（含自动生成的 rcode）。

### PUT /calendar/{id} - 更新日程

Scope: `calendar.write`

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | int | 是 | 路径参数，日程 ID |
| title | string | 否 | 日程标题（不可传空值） |
| htime | string | 否 | 开始时间（格式必须合法） |
| endtime | string | 否 | 结束时间（必须 >= htime） |
| content | string | 否 | 日程内容（允许清空） |
| hstatus | int | 否 | 状态: 0=待办, 1=已办（只允许这两个值） |
| time_cost | int | 否 | 时间花费（分钟），必须 >= 0 |
| linkid | int | 否 | 关联资源 ID |
| type | int | 否 | 关联类型 |

> 至少提供一个更新字段。

**响应**: 返回更新后的日程数据。

---

## Clients 客户

### GET /clients - 客户列表

Scope: `clients.read`

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 否 | 按名称/编号/联系方式搜索 |
| mark | int | 否 | 标识: 1=单位, 2=个人 |
| type | int | 否 | 类型: 1=签约, 2=意向, 3=潜在, 4=终止 |
| degree | int | 否 | 等级: 1=次要, 2=一般, 3=重要, 4=核心 |
| page | int | 否 | 页码，默认 1 |
| limit | int | 否 | 每页条数，默认 20 |

**响应 data 字段** (列表项):

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 客户 ID |
| name | string | 客户名称 |
| code | string | 客户编码 |
| c_num | string | 客户编号 |
| mark | int | 标识: 1=单位, 2=个人 |
| type | int | 类型: 1=签约, 2=意向, 3=潜在, 4=终止 |
| degree | int | 等级 |
| contact | string | 联系方式 |
| address | string | 地址 |
| industry | string | 行业 ID（逗号分隔） |
| org_id | int | 组织 ID |
| created_at | string | 创建时间 |

### GET /clients/{id} - 客户详情

Scope: `clients.read`

**参数**: 路径参数 `id` (必填)

**响应 data 字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 客户 ID |
| name | string | 客户名称 |
| code | string | 客户编码 |
| c_num | string | 客户编号 |
| mark | int | 标识: 1=单位, 2=个人 |
| type | int | 类型: 1=签约, 2=意向, 3=潜在, 4=终止 |
| degree | int | 等级 |
| contact | string | 联系方式 |
| address | string | 地址 |
| card_num | string | 证件号码 |
| industry | string | 行业 |
| from | int | 来源分类 ID |
| from_text | string | 来源文本 |
| c_start_time | string | 合同起始日期 |
| c_end_time | string | 合同终止日期 |
| org_id | int | 组织 ID |
| created_at | string | 创建时间 |

### GET /clients/{id}/contacts - 客户联系人

Scope: `clients.read`

获取指定客户下的联系人列表。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | int | 是 | 路径参数，客户 ID |

**响应 data 字段** (列表项):

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 联系人 ID |
| name | string | 联系人姓名 |
| mobile | string | 手机号 |
| phone | string | 座机号 |
| email | string | 邮箱 |
| address | string | 地址 |
| position | string | 职位 |
| cl_id | int | 所属客户 ID |
| is_default | int | 是否默认联系人 |

### PATCH /clients/{code} - 更新客户

Scope: `clients.write`

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 否 | 客户名称（不可传空值，最大 200 字） |
| mark | int | 否 | 标识: 1=单位, 2=个人（只允许这两个值） |
| type | int | 否 | 类型: 1=签约, 2=意向, 3=潜在, 4=终止（只允许这四个值） |
| degree | int | 否 | 等级: 1=次要, 2=一般, 3=重要, 4=核心（只允许这四个值） |
| address | string | 否 | 地址（最大 500 字） |
| description | string | 否 | 描述/备注（最大 2000 字） |
| contact | string | 否 | 联系方式（最大 100 字） |
| card_num | string | 否 | 证件号码/统一社会信用代码（最大 50 字） |
| industry | string | 否 | 行业 ID |
| from | int | 否 | 来源分类 ID |
| from_text | string | 否 | 来源文本（最大 100 字） |
| legal_per | string | 否 | 法人代表（单位，最大 50 字） |
| sex | int | 否 | 性别: 0=未知, 1=男, 2=女（只允许这三个值） |
| nation | string | 否 | 民族（个人，最大 30 字） |
| c_start_time | string | 否 | 合同起始日期 |
| c_end_time | string | 否 | 合同终止日期（必须 >= c_start_time） |

**响应**: 返回更新后的客户详情（同 GET /clients/{code}）。

---

## Records 记录

独立于案件/项目的记录操作，通过记录 ID 直接获取和更新。

### GET /records/{id} - 记录详情

Scope: `records.read`

**参数**: 路径参数 `id` (必填, hashid 编码)

**响应 data 字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 记录 ID (hashid) |
| title | string | 标题 |
| content | string | 内容 |
| htime | int | 开始时间（Unix 时间戳） |
| htime_text | string | 开始时间文本 (YYYY-MM-DD HH:mm) |
| endtime | int | 结束时间（Unix 时间戳） |
| endtime_text | string | 结束时间文本 |
| hstatus | int | 状态: 0=待办, 1=已办 |
| hstatus_text | string | 状态文本 |
| type | int | 关联类型: 0=不关联, 1=案件, 2=项目, 3=客户 |
| type_text | string | 关联类型文本 |
| huser | string | 负责人 uid (hashid) |
| huser_text | string | 负责人姓名 |
| assit | string | 协助人 uid 列表 (hashid, 逗号分隔) |
| assit_text | string | 协助人姓名列表 (逗号分隔) |
| time_cost | int | 时间花费（小时，保留1位小数） |
| time_cost_text | string | 时间花费可读格式，如 "1.5小时" |
| linkid | string | 关联 ID (hashid) |
| stage | string | 阶段 ID (hashid) |
| stage_name | string | 阶段名称 |
| creator_name | string | 创建人姓名 |

### PATCH /records/{id} - 更新记录

Scope: `records.write`

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 否 | 标题（不可传空值） |
| content | string | 否 | 内容（允许清空） |
| hstatus | int | 否 | 状态: 0=待办, 1=已办（只允许这两个值） |
| htime | string | 否 | 开始时间 (YYYY-MM-DD HH:mm:ss)，格式必须合法 |
| endtime | string | 否 | 结束时间，必须 >= htime |
| time_cost | int | 否 | 时间花费（分钟），必须 >= 0 |
| stage | string | 否 | 阶段 ID (hashid) |

**响应**: 返回更新后的记录详情（同 GET /records/{id}）。

**权限**: 仅记录负责人 (huser) 可更新。

---

## Projects 项目

### GET /projects - 项目列表

Scope: `projects.read`

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 否 | 按项目名称/编号搜索 |
| pr_status | int | 否 | 项目状态: 1=进行中, 2=已结束 |
| pr_type | int | 否 | 项目类型（category ID） |
| degree | int | 否 | 等级: 0=次要, 1=一般, 2=重要 |
| page | int | 否 | 页码，默认 1 |
| limit | int | 否 | 每页条数，默认 20 |

**响应 data 字段** (列表项):

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 项目 ID（hashid） |
| pr_code | string | 项目编号 |
| pr_name | string | 项目名称 |
| pr_status | int | 状态: 1=进行中, 2=已结束 |
| pr_status_text | string | 状态文本 |
| pr_type | int | 项目类型（category ID） |
| pr_type_text | string | 项目类型文本 |
| degree | int | 等级: 0=次要, 1=一般, 2=重要 |
| degree_text | string | 等级文本 |
| start_time | string | 开始时间 |
| end_time | string | 结束时间 |
| client_name | string | 关联客户名称 |
| host_text | string | 负责人姓名 |
| created_at | string | 创建时间 |

### GET /projects/{code} - 项目详情

Scope: `projects.read`

通过 `pr_code` 获取项目详情，包含项目团队、关联客户及联系人。

**参数**: 路径参数 `code` = `pr_code`（必填）

**响应 data 字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 项目 ID（hashid） |
| pr_code | string | 项目编号 |
| pr_name | string | 项目名称 |
| pr_status | int | 状态: 1=进行中, 2=已结束 |
| pr_status_text | string | 状态文本 |
| pr_type | int | 项目类型（category ID） |
| pr_type_text | string | 项目类型文本 |
| degree | int | 等级: 0=次要, 1=一般, 2=重要 |
| degree_text | string | 等级文本 |
| start_time | string | 开始时间 |
| end_time | string | 结束时间 |
| stage_text | string | 当前阶段 |
| require_des | string | 需求描述 |
| funding | decimal | 经费 |
| mark | string | 备注 |
| workers | array | 项目团队成员 |
| workers[].uid | string | 成员 UID（hashid） |
| workers[].name | string | 成员姓名 |
| workers[].role | int | 角色ID: 8=负责人, 9=协助人 |
| workers[].role_text | string | 角色文本 |
| client | object | 关联客户信息（含联系人），无关联客户时为 null |
| client.id | string | 客户 ID（hashid） |
| client.code | string | 客户编码 |
| client.name | string | 客户名称 |
| client.contacts | array | 客户联系人列表 |
| created_at | string | 创建时间 |

### PATCH /projects/{code} - 更新项目

Scope: `projects.write`

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pr_name | string | 否 | 项目名称（不可传空值，最大 200 字） |
| pr_type | int | 否 | 项目类型（category ID） |
| pr_status | int | 否 | 状态: 1=进行中, 2=已结束（只允许这两个值） |
| start_time | string | 否 | 开始时间 |
| end_time | string | 否 | 结束时间（必须 >= start_time） |
| stage_text | string | 否 | 当前阶段 |
| require_des | string | 否 | 需求描述（最大 2000 字） |
| funding | decimal | 否 | 经费 |
| degree | int | 否 | 等级: 0=次要, 1=一般, 2=重要（只允许这三个值） |
| mark | string | 否 | 备注（最大 500 字） |

> 至少提供一个字段。

**响应**: 返回更新后的项目完整详情。

---

## Finance 财务

> **版本要求**: 高阶版及以上套餐才可使用财务相关接口。

### GET /finance - 财务记录列表

Scope: `finance.read`

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | int | 否 | 状态: 1=待认领, 2=审核中, 3=已通过 |
| charge_type | string | 否 | 收费类型（模糊匹配） |
| page | int | 否 | 页码，默认 1 |
| limit | int | 否 | 每页条数，默认 20 |

**响应 data 字段** (列表项):

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 记录 ID |
| org_id | int | 组织 ID |
| status | int | 状态: 1=待认领, 2=审核中, 3=已通过 |
| status_text | string | 状态文本 |
| payer | string | 付款方 |
| to_payer | string | 收款方 |
| amount | decimal | 金额 |
| currency | string | 币种 |
| charge_type | string | 费用类型 |
| check_no | string | 支票号 |
| confirm_uid | int | 确认人 UID |
| confirm_uid_text | string | 确认人姓名 |
| sk_date | string | 收款日期 |
| files | array | 关联文件 |

### GET /finance/{id} - 财务记录详情

Scope: `finance.read`

**参数**: 路径参数 `id` (必填)

**响应**: 返回单条财务记录的完整字段。

### GET /finance/receivables - 应收款列表

Scope: `finance.read`

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| linktype | int | 否 | 关联类型: 1=案件, 2=项目, 3=客户 |
| linkid | int | 否 | 关联资源 ID |
| page | int | 否 | 页码 |
| limit | int | 否 | 每页条数，默认 20 |

**响应 data 字段** (列表项):

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 应收款 ID |
| linktype | int | 关联类型: 1=案件, 2=项目, 3=客户 |
| linkid | int | 关联资源 ID |
| r_amount | decimal | 应收金额 |
| type | int | 类型: 1=合同律师费, 2=计量收费, 3=风险收费, 4=代付费用, 5=协商增收 |
| type_text | string | 类型文本 |
| r_date | string | 应收日期 |
| records | array | 收款记录列表 |
| records[].amount | decimal | 实收金额 |
| records[].kp_amount | decimal | 开票金额 |
| records[].r_date | string | 收款日期 |

### GET /finance/receivables/{id} - 应收款详情

Scope: `finance.read`

**参数**: 路径参数 `id` (必填)

**响应**: 返回单条应收款的完整数据，含收款记录明细。

### GET /finance/summary - 财务摘要

Scope: `finance.read`

返回当前组织维度的财务汇总数据。

**参数**: 无

**响应 data 字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| total_receivable | decimal | 应收总额 |
| total_received | decimal | 已收总额 |
| total_unreceived | decimal | 未收总额 |
| total_expense | decimal | 支出总额 |
| this_month_received | decimal | 本月收款 |
| this_month_expense | decimal | 本月支出 |

> 注: 具体字段以实际返回为准。

---

## Search & Enums 搜索与枚举

### GET /search - 统一搜索

Scope: `cases.read`

跨资源搜索案件名称、当事人、案号等。

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 是 | 搜索关键词 |
| type | string | 否 | 搜索范围: case=案件(默认), client=客户, all=全部 |
| limit | int | 否 | 返回条数，默认 10 |

**响应 data 字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| cases | array | 匹配的案件列表（含 id, case_name, type, g_status） |
| clients | array | 匹配的客户列表（含 id, name, mark） |

### GET /enums - 枚举数据字典

Scope: 任意已授权 scope

返回系统中所有枚举定义，供客户端缓存使用。

**参数**: 无

**响应 data 字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| case_type | object | 案件类型: {1:"民事案件", 2:"商事案件", 3:"仲裁案件", 4:"刑事案件", 5:"行政案件"} |
| case_g_status | object | 案件状态: {1:"在办", 2:"结案", 3:"归档"} |
| case_fee_type | object | 收费类型: {1:"定额收费", 2:"风险收费", 3:"计时收费", 4:"计件收费", 5:"免费"} |
| case_unit_type | object | 受理单位: {1:"法院", 2:"检察院", 3:"公安机关", 4:"仲裁机构", 5:"调解机构", 6:"鉴定机构", 7:"行政机构"} |
| case_degree | object | 案件等级: {0:"次要", 1:"一般", 2:"重要"} |
| case_ja_status | object | 结案状态: {0:"其它", 1:"达成诉求", 2:"部分达成诉求", 3:"未达成诉求", 4:"未委托", 5:"终止委托"} |
| record_type | object | 记录关联类型: {0:"不关联", 1:"案件", 2:"项目", 3:"客户"} |
| record_hstatus | object | 记录状态: {0:"待办", 1:"已办"} |
| client_mark | object | 客户标识: {1:"单位", 2:"个人"} |
| client_type | object | 客户类型: {1:"签约", 2:"意向", 3:"潜在", 4:"终止"} |
| client_degree | object | 客户等级: {1:"次要", 2:"一般", 3:"重要", 4:"核心"} |
| finance_status | object | 财务状态: {1:"待认领", 2:"审核中", 3:"已通过"} |
| receivable_type | object | 应收类型: {1:"合同律师费", 2:"计量收费", 3:"风险收费", 4:"代付费用", 5:"协商增收"} |

---

## V1 兼容说明

### 端点变更

| V1 | V2 | 变化 |
|----|----|------|
| PUT /cases/{id} | PATCH /cases/{id} | 方法改为 PATCH |
| GET /calendar | GET /calendar | 新增 isTeam 团队视图参数 |
| POST /calendar | POST /calendar | 无变化 |
| POST /documents/generate | (保留) | V2 不再迭代，仍可用 |

### Scope 变更

| V1 Scope | V2 Scope | 说明 |
|----------|----------|------|
| cases.read | cases.read | 无变化 |
| cases.write | cases.write | 无变化 |
| calendar.sync | calendar.read + calendar.write | 拆分为读写两个 |
| documents.generate | documents.generate | 保留，V2 不迭代 |
| finance.read | finance.read | 无变化 |
| (新增) | clients.read | V2 新增 |
| (新增) | clients.write | V2 新增 |
| (新增) | projects.read | V2 新增 |
| (新增) | projects.write | V2 新增 |
| (新增) | dashboard.read | V2 新增 |

> 旧 `calendar.sync` 等效于同时拥有 `calendar.read` + `calendar.write`。

### V2 新增端点

- GET /dashboard
- GET /team/members (团队成员列表)
- PATCH /cases/{id} (替代 PUT)
- GET /cases/{id}/stages
- GET /cases/{id}/records
- POST /cases/{id}/records
- PUT /calendar/{id}
- DELETE /calendar/{id}
- GET /clients
- GET /clients/{id}
- GET /clients/{id}/contacts
- GET /projects
- GET /projects/{code}
- PATCH /projects/{code}
- GET /finance/receivables
- GET /finance/receivables/{id}
- GET /finance/summary
- GET /search
- GET /enums

---

## Scope 权限对照表

| Scope | 说明 | 涉及端点 |
|-------|------|----------|
| cases.read | 查看案件列表、详情、搜索 | GET /cases, GET /cases/{id}, GET /cases/{id}/stages, GET /cases/{id}/records, GET /search |
| cases.write | 更新案件、添加办案记录 | PATCH /cases/{id}, POST /cases/{id}/records |
| calendar.read | 查看日程和团队成员 | GET /team/members, GET /calendar |
| calendar.write | 创建/更新/日程 | POST /calendar, PUT /calendar/{id}, DELETE /calendar/{id} |
| clients.read | 查看客户信息和联系人 | GET /clients, GET /clients/{id}, GET /clients/{id}/contacts |
| projects.read | 查看项目列表和详情 | GET /projects, GET /projects/{code} |
| projects.write | 更新项目信息 | PATCH /projects/{code} |
| finance.read | 查看财务记录和摘要 | GET /finance, GET /finance/{id}, GET /finance/receivables, GET /finance/receivables/{id}, GET /finance/summary |
| dashboard.read | 每日概览 | GET /dashboard |
| documents.generate | 生成文书模板 | POST /documents/generate (V1 保留) |
