# MCP 本地源码工具服务器

基于 Model Context Protocol (MCP) 的 Python 工具服务器，支持 stdio 模式通信，提供按全限定类名检索本地 Java 源码的能力。

## 提供的工具

### 1. get_class_source_code
根据全限定类名查找 Java 源码并返回文本内容。支持同时查询多个类（逗号分隔）。

**参数：**
- `class_names`：多个全限定类名，使用逗号分隔（必填）

**使用示例：**
```json
{
  "class_names": "com.example.demo.App, com.foo.bar.UserService"
}
```

### 2. list_project_dirs
列出当前工作空间（由 `--workspace` 指定）下的一级目录。

**参数：** 无

**返回格式（示例）：**
```
/Users/zjh/IdeaProjects/demo1
/Users/zjh/IdeaProjects/demo2
```

## 快速使用

直接从远程仓库运行：

```bash
uv tool run --from git+https://github.com/zjh7890/local-mcp.git local-mcp-server --workspace "/Users/zjh/IdeaProjects" 
```

## Claude Desktop 配置

在 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "local-mcp": {
      "command": "uv",
      "args": [
        "tool",
        "run",
        "--from",
        "git+https://github.com/zjh7890/local-mcp.git",
        "local-mcp-server",
        "--workspace",
        "/Users/zjh/IdeaProjects"
      ]
    }
  }
}
```

## 说明

- 需要通过 CLI 参数 `--workspace` 显式指定工作空间根目录
- 使用系统 `find` 命令检索源码文件（macOS/Linux 可用）

## 许可证

MIT License



