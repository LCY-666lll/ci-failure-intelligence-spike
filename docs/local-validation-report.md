# 本地验证记录

验证日期：2026-10-13

## 已通过

- 隔离 Python 3.11 环境中单元测试 11 项全部通过。
- Linux/amd64 Docker 镜像成功构建，应用以非 root 用户运行。
- API 容器硬限制为 512 MiB；完整请求后的观测内存约 107 MiB。
- PostgreSQL 17 与 Qdrant 1.15 健康检查通过。
- 真实 pytest 失败生成 JUnit XML，经 HMAC 验证后成功入库。
- Qdrant 成功写入向量并返回相似失败结果。
- 重建 API 容器后，PostgreSQL 中的历史运行仍可读取。
- 就绪接口能分别报告 PostgreSQL 与 Qdrant 状态。

## 验证中发现并修复

- XML 元素的布尔语义导致失败节点被漏判；改为显式判断 `None` 并加入回归测试。
- 就绪接口在依赖均正常时仍显示 `not_ready`；改为基于依赖状态显式计算并加入回归测试。

## 尚未通过

- 外部 Neon PostgreSQL 连接。
- 外部 Qdrant Cloud 连接。
- Render 免费实例构建、HTTPS 与休眠冷启动。
- GitHub Actions 对公网服务提交真实报告。
- 公网应用重新部署后的数据持久性。

因此当前结论仅为“本地受限资源部署链路通过”，还不能宣称公网零成本部署通过。
