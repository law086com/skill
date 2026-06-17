# 案件云 AI Agent Skill

让 AI 通过自然语言操作案件云系统 —— 查询案件、管理日程、查看客户、更新记录等。

## 这是什么

这是一个 [AI Agent](https://docs.anthropic.com/en/docs/claude-code) 的自定义 Skill，通过案件云 Open API 实现自然语言交互。

用户只需说"查询我的案件"、"今天有什么安排"、"更新客户信息"，AI 即可自动调用对应 API 完成操作。

## 快速开始

### 1. 安装

将本目录复制到你的 AI Agent（openclaw、hermes、workbody、claudecode等） skills 目录下：

```bash
cp -r skill/ ~/.claude/skills/law086/
```


### 2. 配置

复制 `.env.example` 为 `.env`，填入你的 PAT Token：

```bash
cp .env.example .env
```

编辑 `.env`：

```
# 生产环境
API_BASE_URL=https://open.law086.com/api/v1

# 在案件云 OA「个人设置 > AI管理」中生成 PAT
PAT_TOKEN=law086_pat_你的令牌
```

### 3. 生成 PAT Token

1. 登录案件云 OA: https://oa.law086.com
2. 进入 **个人设置 > AI管理**
3. 点击"生成新令牌"，选择权限范围
4. 复制 Token（以 `law086_pat_` 开头）到 `.env`

### 4. 更新 Skill

**⚠️ 不要删除重装！** 删除会丢失 `.env` 配置（包括 PAT Token），导致需要重新生成。

正确方式 — 进入 skill 目录拉取更新：

```bash
cd ~/.claude/skills/law086/ && git pull
```

`.env` 文件不在 git 管理范围内，`git pull` 不会覆盖你的配置。

### 5. 使用

在 AI Agent 中直接用自然语言：

| 你说 | AI 做什么 |
|------|-----------|
| "查询我的案件" | 调用案件列表 API |
| "今天有什么安排" | 查询今日日程 |
| "创建一个明天下午2点的日程" | 创建日程 |
| "查看客户张三" | 搜索客户 |
| "把记录标记为已办" | 更新记录状态 |
| "案件云" | 显示每日概览 |

## 支持的功能

| 模块 | Scope | 说明 |
|------|-------|------|
| Dashboard | dashboard.read | 每日概览（日程、待办、案件动态） |
| Cases | cases.read / cases.write | 案件列表、详情、阶段、办案记录、更新案件、附件管理 |
| Calendar | calendar.read / calendar.write | 日程查询（个人/团队）、创建、更新 |
| Clients | clients.read / clients.write | 客户列表、详情、联系人、更新客户 |
| Records | records.read / records.write | 独立记录查看、更新（标记已办等） |
| Projects | projects.read / projects.write | 项目列表、详情、更新 |
| Finance | finance.read | 财务记录、应收款、摘要（高阶版） |
| Search | cases.read | 跨资源统一搜索 |
| Enums | - | 枚举数据字典 |

## 目录结构

```
law086/
├── SKILL.md                    # Skill 定义文件（AI Agent 读取）
├── .env.example                # 环境配置模板
├── scripts/
│   └── api.py                  # API 调用脚本（自动处理认证和编码）
└── references/
    └── api-reference.md        # 完整 API 参考文档
```

## API 调用脚本

`scripts/api.py` 是统一 API 调用入口，自动处理认证、中文编码和错误格式化：

```bash
# GET 请求
python3 scripts/api.py GET /cases
python3 scripts/api.py GET "/cases?keyword=张三"

# POST 请求（中文直接写，无需担心编码）
python3 scripts/api.py POST /calendar '{"title":"开庭","htime":"2026-05-10 14:00","endtime":"2026-05-10 15:00"}'

# PATCH 请求
python3 scripts/api.py PATCH /records/abc123 '{"hstatus":1}'
```

## 数据权限

| 空间类型 | 角色 | 可见范围 |
|----------|------|---------|
| 个人空间 | 本人 | 全部个人数据 |
| 团队/律所 | 管理员/拥有者 | 全部组织数据 |
| 团队/律所 | 普通成员 | 只能看自己参与的数据 |
| 律所顶层 + 拥有者（需服务端开启全所范围） | 律所拥有者 | **全所范围**：顶层律所 + 所有直接子团队 org 的案件/客户/项目/财务/合同/日程/记录等读端点（扁平一层，覆盖全部读端点） |

> **律所拥有者全所范围**：当服务端开启 `pat.firm_scope_enabled` 后，律所拥有者（顶层律所 org + OWNER 角色）的 PAT 调用读端点（GET 类）时可见范围自动展开为「顶层律所 + 所有直接子团队 org」。
> - 写端点（创建/更新/上传/合同创建等）仍按 PAT 主 org_id 归属，**不**跨子团队写。
> - 非 owner（普通成员/团队管理员）PAT 行为**零变化**。
> - owner 角色被撤销后最多 60s 内收缩为单 org。
> - 组织结构目前仅支持扁平一层；多级团队（律所→部门→小组）的递归展开为二期。

## 技术栈

- **API**: 案件云 Open API V2.0
- **认证**: PAT (Personal Access Token)
- **协议**: HTTPS + JSON
- **Base URL**: `https://open.law086.com/api/v1`

## License

MIT
