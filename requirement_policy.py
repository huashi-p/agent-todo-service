CATEGORY_POLICY = {
    "technical_skill": {
        "matchable": True,
        "plan_eligible": True,
        "label": "技术技能",
        "exclusion_reason": "",
    },
    "tool_skill": {
        "matchable": True,
        "plan_eligible": True,
        "label": "工具技能",
        "exclusion_reason": "",
    },
    "domain_knowledge": {
        "matchable": True,
        "plan_eligible": True,
        "label": "行业知识",
        "exclusion_reason": "",
    },
    "experience": {
        "matchable": True,
        "plan_eligible": True,
        "label": "实践经历",
        "exclusion_reason": "",
    },
    "education": {
        "matchable": True,
        "plan_eligible": False,
        "label": "学历资格",
        "exclusion_reason": "学历要求只判断资格，不生成学习计划",
    },
    "certificate": {
        "matchable": True,
        "plan_eligible": False,
        "label": "证书资格",
        "exclusion_reason": "证书要求只判断资格，不生成普通技能计划",
    },
    "soft_skill": {
        "matchable": False,
        "plan_eligible": False,
        "label": "软技能",
        "exclusion_reason": "软技能不基于简历做匹配",
    },
    "motivation_attitude": {
        "matchable": False,
        "plan_eligible": False,
        "label": "主观态度",
        "exclusion_reason": "性格、动机和态度不做简历匹配",
    },
    "work_condition": {
        "matchable": False,
        "plan_eligible": False,
        "label": "工作条件",
        "exclusion_reason": "加班、调休、出差等工作条件需本人确认",
    },
    "non_learning_constraint": {
        "matchable": False,
        "plan_eligible": False,
        "label": "非学习要求",
        "exclusion_reason": "该要求不属于可学习技能",
    },
    "unknown": {
        "matchable": False,
        "plan_eligible": False,
        "label": "无法分类",
        "exclusion_reason": "无法可靠分类，默认不参与匹配",
    },
}


CATEGORY_DEFINITIONS = {
    "technical_skill": (
        "可以学习和练习的技术能力，例如 Python、RAG"
    ),
    "tool_skill": (
        "可以操作和练习的工具，例如 Excel、Figma、Docker"
    ),
    "domain_knowledge": (
        "具体行业知识，例如跨境电商平台规则、库存管理"
    ),
    "experience": (
        "需要实际工作或项目经历支撑的要求"
    ),
    "education": (
        "学历、专业等候选人资格要求"
    ),
    "certificate": (
        "明确证书要求，例如 CET-6"
    ),
    "soft_skill": (
        "沟通、表达、团队合作等行为特征"
    ),
    "motivation_attitude": (
        "热爱行业、积极、责任心、抗压等主观态度"
    ),
    "work_condition": (
        "加班、调休、出差、轮班、驻场、地点等条件"
    ),
    "non_learning_constraint": (
        "薪资、到岗时间等非学习要求"
    ),
    "unknown": (
        "无法可靠分类的要求，默认不匹配"
    ),
}


def get_category_policy(category):
    return CATEGORY_POLICY.get(
        category,
        CATEGORY_POLICY["unknown"],
    )


def is_evidence_matchable(category):
    return bool(
        get_category_policy(category)["matchable"]
    )


def is_plan_eligible(category):
    return bool(
        get_category_policy(category)["plan_eligible"]
    )
