# AutoGen Multi-Agent LTV Engine Demo

> 说明：本仓库是用于提交材料的 **模拟 / Demo 工程**，展示“以 AutoGen 多智能体思想为核心的企业级私域运营系统”的架构、运行日志与工作流。示例数据、用户 ID、复购率与成本下降等指标均为演示口径，不代表真实生产经营数据。

## 项目概览

本 demo 构建了一个私域运营 LTV 最大化引擎，围绕「洞察 -> 触达 -> 转化 -> 复盘」增长闭环组织多智能体工作流。

架构采用双层 Agent：

- `OrchestratorAgent`：上层编排智能体，监听用户实时事件，调度专家智能体，选择干预策略。
- `ProfileParserAgent`：用户画像解析专家，识别客群、流失风险、复购倾向。
- `CopywriterAgent`：个性化话术专家，生成符合品牌调性的沟通内容。
- `OfferMatcherAgent`：优惠策略匹配专家，组合权益、积分提醒、专属券与沟通时机。
- `PromptOptimizerAgent`：反馈优化专家，依据转化反馈微调策略权重，模拟强化学习式优化。

## 运行方式

```powershell
cd private-domain-ltv-autogen-demo
python -m src.ltv_engine_demo.main
```

运行后会生成：

- `artifacts/terminal_run_log.txt`：终端运行日志，可作为提交材料之一。
- `artifacts/workflow_trace.json`：Agent 编排过程结构化记录。
- `docs/agent_workflow.svg`：Agent 工作流示意图。
- `docs/workflow.mmd`：Mermaid 工作流源码。

## 示例输出

日志会展示如下流程：

1. 接收用户行为事件，如浏览未下单、积分即将过期、沉默 21 天。
2. 编排智能体调用画像、话术、优惠三个专家智能体。
3. LTV 引擎根据流失风险与复购潜力选择触达策略。
4. 模拟用户反馈并更新 Prompt / 策略权重。
5. 输出分层触达汇总与复盘指标。

## GitHub 提交建议

```powershell
git init
git add .
git commit -m "Add AutoGen-style multi-agent LTV engine demo"
```

然后在 GitHub 新建空仓库，按页面提示执行：

```powershell
git remote add origin https://github.com/<your-name>/private-domain-ltv-autogen-demo.git
git branch -M main
git push -u origin main
```

提交材料可引用：

- 仓库链接
- `artifacts/terminal_run_log.txt`
- `docs/agent_workflow.svg`

