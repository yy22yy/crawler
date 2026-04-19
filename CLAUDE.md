# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

本项目是一个土地交易数据智采系统，通过从 RPA 到 AI Agent 的五次迭代，实现了针对政务及土地交易平台的数据采集技术演进。核心目标是从复杂动态加载、Shadow DOM 限制、非结构化表格中提取金融级数据。

## 核心架构

### 主要模块
- **AI Agent 核心逻辑** (`task3/yy22yy/python_大模型调用/task3_model.py`): 集成 Qwen API 进行语义提取，实现从非结构化公告到标准 Excel 字段的映射
- **实时监控引擎** (`task4/yy22yy/task4.py`): 实现 15s 自动检测序列号，状态变更时触发 SMTP 邮件通知
- **多城市配置中心** (`task3/yy22yy/python_OCR/city_config.json`): 管理广东省各城市的 XPath 配置信息
- **依赖管理** (`task4/yy22yy/requirements.txt`): 定义项目所需 Python 包

### 技术栈
- **Web 自动化**: Selenium (处理复杂交互)
- **多模态识别**: Qwen 大模型 (处理 Shadow DOM 穿透)
- **数据处理**: Pandas (结构化数据输出)
- **通知系统**: SMTP (邮件预警)
- **配置管理**: JSON 配置文件

## 常用开发命令

### 环境设置
```bash
# 安装项目依赖
pip install -r task4/yy22yy/requirements.txt

# 运行 AI Agent 核心逻辑
python task3/yy22yy/python_大模型调用/task3_model.py

# 运行实时监控引擎
python task4/yy22yy/task4.py
```

### 配置要求
- 需要配置 `config.py` 文件（包含 API_URL 和 API_TOKEN）
- 需要配置 SMTP 邮件参数（SENDER_EMAIL, SENDER_AUTH_CODE, RECEIVER_EMAIL）

## 项目结构说明

### 关键文件位置
- **AI 核心逻辑**: `task3/yy22yy/python_大模型调用/task3_model.py`
- **监控引擎**: `task4/yy22yy/task4.py`
- **城市配置**: `task3/yy22yy/python_OCR/city_config.json`
- **依赖文件**: `task4/yy22yy/requirements.txt`

### 模块间关系
- `task3_model.py` 依赖 `city_config.json` 进行多城市处理
- `task4.py` 独立运行，实现实时监控功能
- 两个模块共享基础依赖（Selenium, Pandas 等）

## 开发注意事项

- 项目采用迭代式开发，每个版本解决特定技术痛点
- 当前版本（V5）重点解决 Shadow DOM 穿透和 LLM 内嵌设计
- 代码结构遵循模块化设计，便于维护和扩展
- 需要配置正确的 API 访问权限和环境变量