#!/usr/bin/env python3
"""
MCP 本地工具服务器（local-mcp）
提供 get_class_source_code 工具，按全限定类名从本地工作空间读取 Java 源码。

特性：
- 兼容 MCP stdio 模式
- 与 greeting-mcp 一致的类源码查找与校验逻辑
- 与 time 项目一致的入口结构，便于 uv 远程执行
"""

import argparse
import asyncio
import logging
import os
import subprocess
import sys
from typing import List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool


# -------------------- 全局配置 --------------------

DEFAULT_SEARCH_BASE_PATH = "/Users/zjh/IdeaProjects"
SEARCH_BASE_PATH: str = DEFAULT_SEARCH_BASE_PATH


def log_to_stderr(message: str) -> None:
    try:
        print(message, file=sys.stderr, flush=True)
    except Exception:
        pass


# -------------------- 工具元数据 --------------------

server = Server("local-mcp-server")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """列出所有可用工具"""
    return [
        Tool(
            name="get_class_source_code",
            description=(
                "根据全限定类名在用户本地目录获取类的源码信息。支持同时查询多个类名，用逗号分隔。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "class_names": {
                        "type": "string",
                        "description": "多个全限定类名，逗号分隔"
                    }
                },
                "required": ["class_names"]
            }
        ),
        Tool(
            name="list_project_dirs_local",
            description=(
                "列出用户本地的项目列表，按绝对路径逐行返回。"
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
    ]


# -------------------- 业务实现（与 greeting-mcp 对齐） --------------------

def get_class_source_code_local(class_names: str) -> str:
    if not class_names or not class_names.strip():
        return "错误：类名不能为空"

    base_path = (SEARCH_BASE_PATH).strip() or DEFAULT_SEARCH_BASE_PATH

    class_name_list = [name.strip() for name in class_names.split(",") if name.strip()]

    results: list[str] = []
    for class_name in class_name_list:
        source_code = get_class_source_code_string(class_name, base_path)
        if source_code == "Not Found":
            results.append(f"{class_name}:\nNot Found")
        else:
            results.append(f"{class_name}:\n{source_code}")

    return "\n\n".join(results)


def get_class_source_code_string(class_name: str, search_base: str) -> str:
    try:
        java_file_path = find_java_file(class_name, search_base)
        if not java_file_path:
            return "Not Found"

        content = read_file_content(java_file_path)
        if not content:
            return "Not Found"

        if not validate_package_match(content, class_name):
            return "Not Found"

        return content
    except Exception as e:
        log_to_stderr(f"获取类源码时发生错误: {e}")
        return "Not Found"


def find_java_file(class_name: str, search_base: str) -> Optional[str]:
    try:
        simple_class_name = get_simple_class_name(class_name)
        java_file_name = f"{simple_class_name}.java"

        cmd = ["find", search_base, "-name", java_file_name, "-type", "f"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            log_to_stderr(f"搜索文件失败: {result.stderr}")
            return None

        file_paths = [path.strip() for path in result.stdout.strip().split('\n') if path.strip()]

        if not file_paths:
            return None

        if len(file_paths) == 1:
            return file_paths[0]

        return select_best_match_file(file_paths, class_name)
    except Exception as e:
        log_to_stderr(f"查找文件时发生错误: {e}")
        return None


def select_best_match_file(file_paths: List[str], class_name: str) -> Optional[str]:
    if len(file_paths) == 1:
        return file_paths[0]

    best_file: Optional[str] = None
    best_score = -1

    for file_path in file_paths:
        try:
            content = read_file_content(file_path)
            if content and validate_package_match(content, class_name):
                score = calculate_path_score(file_path, class_name)
                if score > best_score:
                    best_score = score
                    best_file = file_path
        except Exception as e:
            log_to_stderr(f"验证文件 {file_path} 时发生错误: {e}")
            continue

    return best_file if best_file else file_paths[0]


def calculate_path_score(file_path: str, class_name: str) -> int:
    try:
        package_name = extract_package_name(class_name)
        if not package_name:
            return 0

        package_parts = package_name.split('.')
        score = 0
        for part in package_parts:
            if f"/{part}/" in file_path:
                score += 1
        return score
    except Exception:
        return 0


def validate_package_match(content: str, class_name: str) -> bool:
    try:
        expected_package = extract_package_name(class_name)
        if not expected_package:
            return True

        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('package ') and line.endswith(';'):
                actual_package = line[8:-1].strip()
                return actual_package == expected_package

        return False
    except Exception as e:
        log_to_stderr(f"验证包名匹配时发生错误: {e}")
        return False


def read_file_content(file_path: str) -> Optional[str]:
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        log_to_stderr(f"读取文件 {file_path} 时发生错误: {e}")
        return None


def get_simple_class_name(class_name: str) -> str:
    if '.' in class_name:
        return class_name.split('.')[-1]
    return class_name


def extract_package_name(class_name: str) -> str:
    if '.' in class_name:
        return '.'.join(class_name.split('.')[:-1])
    return ""


def list_project_dirs_local() -> str:
    try:
        base_path = (SEARCH_BASE_PATH).strip() or DEFAULT_SEARCH_BASE_PATH
        entries = os.listdir(base_path)
        dir_paths: list[str] = []
        for name in sorted(entries):
            full_path = os.path.join(base_path, name)
            if os.path.isdir(full_path):
                dir_paths.append(full_path)
        return "\n".join(dir_paths)
    except Exception as e:
        log_to_stderr(f"列出工作空间目录时发生错误: {e}")
        return ""


# -------------------- 工具调用处理 --------------------


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list:
    if name == "get_class_source_code":
        try:
            class_names = arguments["class_names"]
            result_text = get_class_source_code_local(class_names)
            return [{"type": "text", "text": result_text}]
        except Exception as e:
            return [{"type": "text", "text": f"错误: {str(e)}"}]

    if name == "list_project_dirs_local":
        try:
            result_text = list_project_dirs_local()
            return [{"type": "text", "text": result_text}]
        except Exception as e:
            return [{"type": "text", "text": f"错误: {str(e)}"}]

    return [{"type": "text", "text": f"未知工具: {name}"}]


# -------------------- 启动/CLI --------------------


def set_workspace_from_cli_and_env() -> None:
    global SEARCH_BASE_PATH
    workspace_env = os.getenv("WORKSPACE")
    SEARCH_BASE_PATH = ((workspace_env or DEFAULT_SEARCH_BASE_PATH).strip() or DEFAULT_SEARCH_BASE_PATH)
    log_to_stderr(f"工作空间已设置: {SEARCH_BASE_PATH}")


async def main_async() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def cli_main() -> None:
    parser = argparse.ArgumentParser(description="local-mcp 服务器")
    parser.parse_args()

    try:
        set_workspace_from_cli_and_env()
        asyncio.run(main_async())
    except KeyboardInterrupt:
        log_to_stderr("服务器已停止")
    except Exception as e:
        log_to_stderr(f"服务器运行时发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli_main()


