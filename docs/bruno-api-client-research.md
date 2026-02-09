# Bruno API 客户端调研报告

> 最后更新：2025-02-10

## 📊 Bruno 简介

**Bruno** 是一个开源的、Git 友好的 API 客户端，作为 Postman 的轻量级替代方案。它的核心理念是"文件即项目"，所有 API 请求都以 YAML 文件形式存储在本地。

### 核心特性

- **开源免费**：MIT 许可证，无需付费订阅
- **Git 原生支持**：API 定义以可读文件存储，天然支持版本控制
- **数据隐私**：所有数据存储在本地，不上传云端
- **完全离线**：无需账号登录，可离线使用
- **轻量快速**：基于 Electron 构建，启动速度快

## 🎯 主要使用场景

### 1. 团队协作与 API 版本控制

- ✅ API 定义与代码一起管理，通过 Git 追踪所有变更
- ✅ 支持代码审查（Code Review）API 修改
- ✅ 团队成员可轻松共享 API 集合
- ✅ 分支管理不同环境的 API 配置

**适用项目类型**：
- 微服务架构
- 前后端分离项目
- 需要严格版本控制的 API 项目

### 2. 接口自动化测试

- ✅ 支持编写测试脚本和链式 API 调用
- ✅ 可集成到 CI/CD 流程（GitHub Actions）
- ✅ 使用 Bruno CLI 进行批量自动化测试
- ✅ 支持环境变量和动态参数

**典型应用**：
- 回归测试
- API 健康检查
- 性能测试
- 集成测试

### 3. REST API 开发与调试

- ✅ 本地开发环境下的 API 测试
- ✅ 完全离线工作，无需账号登录
- ✅ 支持环境变量管理
- ✅ 响应数据可视化

### 4. 注重隐私的项目

- ✅ 所有数据存储在本地文件系统
- ✅ 不会上传到云端服务器
- ✅ 适合金融、医疗等敏感行业
- ✅ 符合数据合规要求

## 🏆 最佳实践

### 1. 项目结构组织

推荐的标准目录结构：

```
project/
├── bruno/
│   ├── collections/
│   │   └── my-api/
│   │       ├── users/
│   │       │   ├── login.bru
│   │       │   ├── register.bru
│   │       │   └── get-profile.bru
│   │       ├── products/
│   │       │   ├── list.bru
│   │       │   ├── create.bru
│   │       │   └── delete.bru
│   │       └── environments/
│   │           ├── development.bru
│   │           ├── staging.bru
│   │           └── production.bru
├── docs/
│   └── api-testing-guide.md
└── src/
```

### 2. 环境变量管理

**CLI 切换环境**：
```bash
# 开发环境
bru run --env development

# 预发布环境
bru run --env staging

# 生产环境
bru run --env production
```

**环境文件示例**（environments/development.bru）：
```yaml
dev: {
  "base_url": "http://localhost:3000",
  "api_key": "dev-key-123"
}
```

### 3. API 链式调用

使用响应数据作为下一个请求的参数：

```javascript
// 第一个请求：获取最新记录
// Response: { "id": 123, "name": "test" }

// 第二个请求：使用返回的 id
// URL: /api/foo/{{id}}
// 在 Tests 脚本中：
bru.setEnvVar("id", res.body.id);
```

### 4. 版本控制工作流

**推荐的 Git 工作流**：

1. **主分支**：存储生产环境的 API 配置
2. **开发分支**：开发新功能的 API
3. **功能分支**：从 develop 分支创建，完成后通过 PR 合并

**PR 审查清单**：
- API 路径变更是否合理
- 请求参数是否符合规范
- 是否添加了必要的测试脚本
- 环境变量是否正确配置

### 5. CI/CD 集成

**GitHub Actions 示例**：

```yaml
name: API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install Bruno
        run: |
          npm install -g @usebruno/cli
      - name: Run API Tests
        run: |
          bru run --env testing
```

### 6. 调试技巧

- 使用 `console.log()` 在脚本中输出调试信息
- 利用 Bruno 的响应查看器进行调试
- 使用环境变量隔离不同环境的数据
- 利用 Git 历史回滚错误的 API 修改

## 🌟 核心优势对比

### Bruno vs Postman

| 特性 | Bruno | Postman |
|------|--------|---------|
| 开源免费 | ✅ MIT 许可 | ❌ 付费订阅 |
| Git 集成 | ✅ 原生支持 | ⚠️ 有限支持 |
| 数据隐私 | ✅ 本地存储 | ❌ 云端同步 |
| 离线使用 | ✅ 完全离线 | ❌ 需登录 |
| 团队协作 | ✅ 通过 Git | ✅ 云端同步 |
| API 链式调用 | ✅ 支持 | ✅ 支持 |
| 测试脚本 | ✅ 支持 | ✅ 支持 |
| CLI 工具 | ✅ 完整支持 | ✅ 支持 |
| 学习曲线 | ⚠️ 相对较新 | ✅ 成熟文档 |
| 第三方集成 | ⚠️ 较少 | ✅ 丰富 |

## 📦 现成的项目案例

### 1. Bruno API Test Starter

- **GitHub**: [Automation-Test-Starter/Bruno-API-Test-Starter](https://github.com/Automation-Test-Starter/Bruno-API-Test-Starter)
- **特点**：
  - 提供完整的 API 测试入门模板
  - 包含集合组织和请求示例
  - 适合快速上手

### 2. 官方资源

- [GitHub Discussions - API 调用链最佳实践](https://github.com/usebruno/bruno/discussions/942)
- [CI/CD 自动化指南](https://blog.usebruno.com/automating-api-testing-github-actions)
- [GitHub Copilot 集成教程](https://blog.usebruno.com/supercharged-api-client-using-bruno-with-github-copilot)
- [版本控制教程](https://blog.usebruno.com/version-control-with-bruno-and-github)

### 3. 实际应用场景

- **微服务架构**：测试多个服务间的 API 调用
- **前后端分离**：前端团队独立调试后端接口
- **自动化回归测试**：集成到 CI/CD 流程
- **API 文档生成**：通过代码生成文档

## ⚠️ 局限性与注意事项

### 局限性

- ❌ 仅支持桌面应用（无 Web 版）
- ❌ 复杂场景配置可能不如 Postman 成熟
- ❌ 生态系统相对较新，社区资源较少
- ❌ 第三方集成和插件支持有限

### 注意事项

1. **团队适应性**：团队需要熟悉 Git 工作流
2. **备份策略**：依赖 Git 进行备份，需要良好的版本控制习惯
3. **学习成本**：对于习惯了 Postman 的团队，需要一定的学习时间
4. **企业支持**：没有企业版和技术支持服务

## 🎓 学习资源

### 官方资源

- **官网**: https://www.usebruno.com/
- **GitHub**: https://github.com/usebruno/bruno
- **文档**: https://docs.usebruno.com/

### 中文教程

- [从 0 到 1 搭建 Bruno 接口自动化测试项目](https://juejin.cn/post/7327284192647266358)
- [5分钟上手 Bruno 请求自动化](https://blog.gitcode.com/d6174db0c92ce212fe9c12d51f928ba6.html)
- [2025 年最受欢迎的 10 款 API 客户端](https://www.cnblogs.com/ifmeme/p/18991880)

### 视频教程

- [Bruno API Collaboration via Git](https://www.youtube.com/watch?v=WY7xquaVEJk)

## 💡 适用场景总结

### 推荐使用 Bruno 的场景

- ✅ 开源项目或预算有限的团队
- ✅ 注重数据隐私和安全的行业
- ✅ 已经使用 Git 进行版本控制的团队
- ✅ 需要将 API 测试纳入 CI/CD 流程
- ✅ 希望离线工作的独立开发者

### 推荐继续使用 Postman 的场景

- ✅ 需要大量第三方集成的企业
- ✅ 团队不熟悉 Git 工作流
- ✅ 需要云端同步和团队协作功能
- ✅ 需要企业级技术支持
- ✅ 复杂的 API 测试场景

## 📝 总结

Bruno 是一个非常适合现代开发流程的 API 客户端，特别适合：

1. **重视数据隐私和安全的团队**
2. **使用 Git 进行版本控制的项目**
3. **预算有限的开源项目**
4. **需要将 API 测试纳入 DevOps 流程的团队**

随着 2025 年的发展，Bruno 已经成为 Postman 的热门替代方案之一。虽然生态系统相对较新，但其 Git 原生支持和数据隐私特性使其在特定场景下具有明显优势。

---

## 参考资料

- [2025 年最受欢迎的 10 款 API 客户端](https://www.cnblogs.com/ifmeme/p/18991880)
- [从 0 到 1 搭建 Bruno 接口自动化测试项目](https://juejin.cn/post/7327284192647266358)
- [Bruno API Test Starter - GitHub](https://github.com/Automation-Test-Starter/Bruno-API-Test-Starter)
- [Version Control with Bruno & GitHub](https://blog.usebruno.com/version-control-with-bruno-and-github)
- [Automate API Testing in CI/CD](https://blog.usebruno.com/automating-api-testing-github-actions)
- [GitHub Copilot 集成教程](https://blog.usebruno.com/supercharged-api-client-using-bruno-with-github-copilot)
