# 大模型安全护栏 | LLM Safety Guardrail

小组合作项目：在大模型对话服务前后加入多层内容检查，并记录各模块的处理过程。核心技术为 FastAPI、vLLM、Qwen2.5-7B-Instruct 和 LoRA 适配器。

本仓库整理自团队公开仓库 [undemo/llm](https://github.com/undemo/llm)。Qristoetle 为小组成员，个人具体分工尚未补充；本仓库保留团队来源，不将全部代码归为个人独立开发。

## 实现内容

- 输入门卫分类、专题内容检查及敏感词检测接口。
- 大模型回答生成、自审查和回答净化。
- vLLM 推理服务，按请求选择 `classify`、`china` LoRA 适配器。
- 对话 API、处理日志、历史日志快照和日志查看页面。

```text
main.py / run.py      对话后端启动入口
vllm_server.py        GPU 推理服务及 LoRA 配置
src/security/        输入检查和输出自审查
src/services/        推理客户端及回答净化
src/routes/          对话、日志和健康检查路由
src/config/          配置、提示词和拒答文本
static/              日志查看页面
docs/                原使用手册、资源说明与整理记录
```

## 模型与训练语料

根据小组发布信息，微调后的模型和训练语料位于 [百度网盘](https://pan.baidu.com/s/1tK-GSp5OOobZWxApgGJDVg)，提取码：`j3s9`。语料文件按发布说明修改后缀为 `.zip` 后解压。

这些大文件没有重复加入 Git 仓库。当前未下载或核验网盘内容，因此未确认具体文件名、权重大小、训练配置和目录结构。代码仓库中没有训练脚本或完整训练数据；有关资源配置见 [资源说明](docs/resources.md)。

## 运行

先安装后端依赖：

```bash
python -m venv .venv
python -m pip install -r requirements.txt
```

完整推理需在支持 vLLM 的 GPU 环境安装对应依赖，准备 Qwen2.5-7B-Instruct 基础模型和两个 LoRA 适配器，再修改 `vllm_server.py` 中的模型与适配器路径。原代码使用 `/root/autodl-tmp/` 路径，需要按自己的环境调整。

回答净化服务的密钥通过环境变量提供。在 Linux 终端设置：

```bash
export DATA_PURIFICATION_API_KEY="填写自己的服务密钥"
export DATA_PURIFICATION_API_BAK_KEY="填写自己的备用密钥"
```

服务地址和模型名称在 `src/config/settings.py` 中配置。`.env.example` 仅列出变量名称；程序不会自动加载 `.env` 文件，需要在启动终端设置环境变量。

分别启动 GPU 推理服务和对话后端：

```bash
python vllm_server.py
python main.py
```

默认对话后端地址：`http://localhost:6006`，API 文档：`http://localhost:6006/docs`，推理服务：`http://127.0.0.1:6007`。完整接口说明见 [原使用手册](docs/README.md)。

## 当前复现范围

本次整理检查 Python 语法、后端导入和不依赖模型的页面/API 路由，没有验证 GPU 推理、模型效果或网盘资源。

原仓库未提供 `program/sensitive/sensitive_optimized.py` 及词表。该模块缺失时，原代码回退为空检测结果，不能将其理解为敏感词检测正常工作。健康接口中的顶层 `status` 也不能单独证明推理服务可用，应结合 `vllm_service` 查看。

本项目是课程与小组研究作品，当前没有随仓库提供可复现的安全评测结果。

## 来源与整理

来源版本、清理记录和验证情况见 [整理记录](docs/migration-notes.md)。原仓库只在 `vllm_server.py` 中含有 Apache 2.0 声明，未提供覆盖全项目的 LICENSE；这里保留原声明，不为整个团队项目新增许可。
