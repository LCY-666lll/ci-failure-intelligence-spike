# 零成本公网部署可行性验证报告

验证日期：2026-10-13

## 结论

CI Failure Intelligence 的核心部署链路已在真实公网环境跑通：GitHub Actions 产生真实失败报告，经 HMAC 鉴权提交到 Render 上的 FastAPI 服务，写入托管 PostgreSQL 和 Qdrant Cloud，并能在全新容器重新部署后继续读取。当前证据足以确认该方向在技术与部署层面可行，不存在阻断项目开发的第三方数据访问或基础设施权限问题。

本次验证全部使用免费方案，未绑定付费实例，也未产生费用。

## 公网环境

- 代码仓库：https://github.com/LCY-666lll/ci-failure-intelligence-spike
- 公网服务：https://ci-failure-intelligence-spike.onrender.com
- Render Web Service：Free，Docker，0.1 CPU / 512 MiB RAM，HTTPS。
- Render PostgreSQL：Free，PostgreSQL 18，1 GiB，Oregon。
- Qdrant Cloud：Free Tier，Qdrant 1.19.2，1 GiB RAM / 0.5 vCPU / 4 GiB 磁盘，Oregon。

## 已通过的验证

### 代码与容器

- 14 项单元测试全部通过。
- Linux/amd64 Docker 镜像成功构建，应用以非 root 用户运行。
- API 容器硬限制为 512 MiB；本地完整请求后的观测内存约 107 MiB。
- 本地 PostgreSQL 与 Qdrant 均使用持久化卷；重建 API 容器后历史运行仍可读取。
- Qdrant Python 客户端升级至 1.19.1，与云端 1.19.2 兼容；最终云部署启动日志无版本不兼容告警。

### 真实 GitHub Actions 链路

- 工作流运行：https://github.com/LCY-666lll/ci-failure-intelligence-spike/actions/runs/38415959319
- pytest 用例真实失败并生成 JUnit XML；该步骤按设计返回退出码 1。
- 后续提交步骤经 HMAC-SHA256 鉴权向公网 API 上传报告。
- 服务返回 `id=1`、`created=true`、`failure_count=1`，并从 Qdrant 返回相似结果。
- 整个工作流最终状态为 Success，耗时 27 秒。

### 云依赖与公网 API

- `GET /health/ready` 返回 HTTP 200，PostgreSQL 与 Qdrant 均为 `ok`。
- `GET /api/v1/ci-runs/1` 返回 HTTP 200，能读取 GitHub Actions 写入的真实运行号 `38415959319` 及失败详情。
- 最终提交 `11417da` 在 Render 部署成功，部署记录为 `dep-db74bfavcj2c7390661g`。
- 在不同的全新 Render 容器进程中重复读取记录成功，证明应用容器无状态、数据由外部 PostgreSQL 持久化。
- Qdrant collection 在重新部署后仍存在，云端访问密钥和网络访问有效。

### 冷启动

- Render 控制台明确标识 Free 实例会在闲置后休眠，首次请求可能延迟 50 秒以上。
- 停止外部访问超过 17 分钟后，对 `/health/ready` 发起首次计时请求。
- 冷启动实测 32.17 秒返回 HTTP 200；响应同时确认 PostgreSQL 与 Qdrant 均为 `ok`。
- 冷启动完成后再次读取 `/api/v1/ci-runs/1` 返回 HTTP 200，历史 CI 数据仍完整存在。

## 验证中发现并修复的问题

- XML 元素的布尔语义导致失败节点漏判：改为显式判断 `None` 并加入回归测试。
- 就绪接口在依赖均正常时仍显示 `not_ready`：改为基于依赖状态显式计算并加入回归测试。
- Render 接受普通 `postgresql://` 连接串，而 async SQLAlchemy 需要 `postgresql+asyncpg://`：在配置层统一规范化。
- 第一次配置 Qdrant 密钥时浏览器剪贴板未写入值，导致云端返回 403：确认是配置错误而非架构问题，补齐密钥后部署成功。
- 初始 qdrant-client 1.15.1 与云端 1.19.2 存在兼容告警：升级并重新构建、测试、部署后消除。

## 免费方案边界

- Render 免费 Web Service 会休眠，因此适合演示、作品集和低频访问，不提供持续低延迟 SLA。
- 本次 Render 免费 PostgreSQL 实例将在 2026-11-12 到期。它只承担部署可行性验证；正式项目必须在到期前备份并迁移到当时仍可用的长期免费 PostgreSQL，或更换托管方案。
- 免费服务条款与额度可能变化，正式上线前需要再次核对，但代码并未绑定 Render 专有接口，PostgreSQL、Qdrant 和 Docker 均可迁移。

## 最终判定

项目方向可以继续。已经实证可行的部分包括：公网 HTTPS、异步 FastAPI、HMAC 机器鉴权、GitHub Actions 集成、关系型持久化、外部向量数据库、相似度检索、容器化部署、依赖健康检查、结构化日志及重新部署后的数据持久性。剩余风险属于免费托管的额度与休眠限制，不是项目架构或开发权限的阻断风险。
