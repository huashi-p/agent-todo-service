# Week 12 搜索引用范围

更新日期：2026-11-19

## 输入

- 处理岗位 JD 中所有可学习的技能缺口。
- Playbook 只作为可选教学骨架，不是生成门槛。
- 每次搜索最多返回 5 条候选。
- 每次最多抓取 3 个候选网址。
- DeepSeek 结合完整 JD 生成 1–3 个具体 `search_topics`。

## 要求分类

- `technical_skill`：技术技能，可以匹配并生成计划。
- `tool_skill`：工具操作，可以匹配并生成计划。
- `domain_knowledge`：具体行业知识，可以匹配并生成计划。
- `experience`：实践经历，可以匹配并生成计划。
- `education`：学历资格，只判断资格，不生成普通技能课程。
- `certificate`：证书资格，只判断资格，不生成普通技能课程。
- `soft_skill`：沟通、团队合作等，不基于简历判断。
- `motivation_attitude`：热爱、积极、责任心、抗压等，不基于简历判断。
- `work_condition`：加班、调休、出差、轮班、驻场等，需本人确认。
- `non_learning_constraint`：地点、到岗时间等非学习要求。
- `unknown`：无法可靠分类，默认不参与匹配和计划生成。

## 输出

- `curated_grounded`
- `generated_grounded`
- `curated_template`
- `model_only`
- `basic_fallback`
- `not_applicable`
- 每个计划项最多保存 3 个来源。
- 不生成计划的要求写入 `planning_exclusions`。

## 来源快照

每个来源包含：

- `source_id`：只能由服务端生成。
- `title`
- `url`：只能来自搜索并成功抓取的来源。
- `final_url`
- `fetched_at`：UTC ISO 8601。
- `excerpt`：实际抓取正文中的连续片段。
- `evidence_quote`：由服务端从 `excerpt` 填入，模型不能提供 URL。
- `search_score`

## 降级

- 有 Playbook，外部资料不可用：`curated_template`。
- 无 Playbook，外部资料不可用、模型成功：`model_only`。
- 无 Playbook，外部资料和模型均失败：`basic_fallback`。
- 可匹配但无直接证据：`missing`。
- 不属于可验证技能或经历：`not_applicable`。
- 正常岗位输入不能因为外部服务失败直接返回 500。

## 禁止

- 模型编造 URL。
- 使用搜索摘要冒充网页正文。
- 模型自行填写 `evidence_quote`。
- 使用登录页、内网页或危险端口。
- 使用搜索结果反推投递状态。
- 把软技能、性格、爱好或工作条件包装成技能课程。
- 把 AI 建议包装成专业认证或医疗、法律、金融结论。
