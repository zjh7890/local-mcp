local-mcp
=========

本项目提供一个 MCP 服务器，包含 `get_class_source_code` 工具，用于通过全限定类名在本地工作空间检索 Java 源码。

- 逻辑参考：`greeting-mcp`
- 结构与运行方式参考：`time` 项目，支持通过 `uv` 直接运行

安装 / 运行
-----------

本地运行（建议 Python 3.10+）：

```bash
uv run -- python -m local_mcp.main --workspace /Users/zjh/IdeaProjects
# 或
uv run -- local-mcp-server --workspace /Users/zjh/IdeaProjects
```

远程运行（示例，需将仓库推送到 GitHub）：

```bash
# 方式一：通过 gh 简写（例如 gh:yourname/local-mcp）
uvx --from gh:yourname/local-mcp local-mcp-server --workspace /Users/zjh/IdeaProjects

# 方式二：通过 https 地址
uvx --from https://github.com/yourname/local-mcp.git local-mcp-server --workspace /Users/zjh/IdeaProjects
```

也可通过设置环境变量 `WORKSPACE` 指定默认搜索根目录：

```bash
export WORKSPACE=/Users/zjh/IdeaProjects
uvx --from gh:yourname/local-mcp local-mcp-server
```

工具说明
--------

- get_class_source_code
  - 入参：
    - `class_names` (string, required): 多个全限定类名，逗号分隔
    - `workspace` (string, optional): 覆盖搜索根目录
    - `code_fence` (boolean, optional, default: true): 是否以 ```java 代码块包裹输出
  - 返回：文本（包含每个类名及源码，或 Not Found）

兼容性
------

- 默认搜索路径：`/Users/zjh/IdeaProjects`
- 可通过 `--workspace` 或 `WORKSPACE` 环境变量覆盖
- 使用 `find` 命令检索源码文件（macOS/Linux 可用）

许可证
----

MIT


