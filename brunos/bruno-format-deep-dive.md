对于习惯了 Postman 或 Insomnia 的开发者来说，**Bruno** 采用的 `.bru` 文件格式非常亲民且极具前瞻性。它本质上是一种**纯文本的类 DSL（领域特定语言）格式**，设计初衷是为了解决传统 API 工具导出的 JSON 文件难以进行 Git 版本管理（Diff 混乱）的问题。

以下是 `.bru` 文件格式的详细分解：

---

## 1. 核心设计理念

- **可读性高**：采用类似 YAML/HCL 的结构，即使不打开 Bruno 客户端，用记事本也能轻松修改。
- **版本控制友好**：每个 API 请求就是一个独立文件，且内容行分明，Git Diff 非常清晰。
- **离线优先**：所有数据都存储在你的本地目录中。

---

## 2. 文件结构概览

一个典型的 `.bru` 文件由多个“块”（Blocks）组成，每个块以 `meta`、`get`、`headers` 等关键词标识。

### A. 基础元数据 (meta)

定义请求的名称、类型和序列号。

```hcl
meta {
  name: 获取用户信息
  type: http
  seq: 1
}

```

### B. 请求方法与 URL

直接以 HTTP 方法命名块，内部定义 URL。

```hcl
get {
  url: {{baseUrl}}/users/:id
}

```

### C. 参数与请求头 (params / headers)

采用简单的键值对形式。

- **query**: URL 查询参数。
- **path**: 路径变量。
- **headers**: HTTP 请求头。

```hcl
params:query {
  page: 1
  limit: 10
}

params:path {
  id: 123
}

headers {
  Authorization: Bearer {{token}}
  Accept: application/json
}

```

### D. 请求体 (body)

根据不同的内容类型，格式略有不同。若是 JSON，直接在块内编写。

```hcl
body:json {
  {
    "username": "fastapi_dev",
    "email": "test@example.com"
  }
}

```

### E. 脚本与断言 (script / assert)

这是 Bruno 强大的地方，支持直接在文件中编写 JavaScript。

- **script:pre-request**: 发送请求前的逻辑。
- **script:post-response**: 收到响应后的逻辑（如设置环境变量）。
- **assert**: 无需编写代码的声明式断言。

```hcl
assert {
  res.status: eq 200
  res.body.id: nne null
}

script:pre-request {
  console.log("准备发送请求...");
}

```

---

## 3. `.bru` 格式 vs Postman JSON

| 特性             | .bru (Bruno)     | .json (Postman)          |
| ---------------- | ---------------- | ------------------------ |
| **可读性**       | 极高，像代码一样 | 较低，嵌套深且多转义字符 |
| **Git 合并冲突** | 容易解决         | 噩梦级别                 |
| **脚本编写**     | 原生 JS 块       | 封装在 JSON 字符串中     |
| **文件组织**     | 一个请求一个文件 | 整个 Collection 一个文件 |

---

## 4. 为什么适合 Python/FastAPI 开发？

作为后端工程师，你可能会发现 `.bru` 格式非常契合你的开发习惯：

1. **代码复用**：你可以直接在 FastAPI 项目根目录下创建一个 `api-tests` 文件夹，将 `.bru` 文件存放在里面。
2. **文档即测试**：`.bru` 文件本身就是一份非常清晰的 API 调用说明文档。
3. **自动化**：可以使用 Bruno 的 CLI 工具 `bru` 直接运行这些文件，轻松集成到 CI/CD 流程中。

> **小技巧**：如果你已有大量的 Postman 集合，Bruno 支持直接导入并将它们批量转换成独立的 `.bru` 文件。

你想了解如何利用 `.bru` 文件中的环境变量来管理 FastAPI 的不同开发环境（如 Dev 和 Staging）吗？

---

## 5. 深入研究 .bru 文件的底层规范或查找特定语法

### 5.1 官方文档（最权威）

Bruno Docs - Bru Language: https://docs.usebruno.com/bru-language-design.html 这里详细介绍了为什么 Bruno 选择了这种类似 HCL 的 DSL 语言，以及它的设计哲学。

Scripting API: https://docs.usebruno.com/scripting/introduction.html 如果你想知道在 .bru 文件的 script 块中可以使用哪些 JS 对象（如 res、req、bru），这里有完整的 API 列表。

### 5.2 GitHub 源代码（最深层）

由于 Bruno 是完全开源的，其 DSL 解析器的实现逻辑直接决定了 .bru 文件的格式边界。

- Lang 仓库: usebruno/bruno 仓库下的 packages/bruno-lang 目录。
  - 你可以看到 bruToJson 和 jsonToBru 的解析逻辑，这是了解“什么可以写在文件里”的最硬核方式。
