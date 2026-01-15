"""
The Last 5% - Agent B: 使用场景"撞墙"预测 (Scenario Agent)
基于用户场景和产品参数，预测可能遇到的问题
"""

import json
from typing import Any
from backend.agents.base_agent import BaseAgent
from backend.models import ScenarioWarning


SCENARIO_SYSTEM_PROMPT = """你是一个产品使用场景分析专家，擅长根据产品参数和用户的实际使用环境，预测可能出现的问题。

## 你的任务
分析用户描述的使用场景，结合产品的技术参数，预判这款产品在该场景下可能"撞墙"的地方。

## 常见的"场景撞墙"类型：

### 环境因素
- 光照条件：投影仪流明 vs 环境光照
- 温度条件：电子产品工作温度范围 vs 实际环境
- 空间尺寸：产品尺寸 vs 可用空间
- 噪音环境：产品噪音 vs 使用场景要求

### 使用强度
- 连续工作时间 vs 产品散热能力
- 日使用频率 vs 产品耐久设计
- 负载强度 vs 产品功率/性能

### 兼容性
- 设备兼容性：接口、协议、系统版本
- 网络环境：WiFi覆盖、网速要求
- 配件通用性：耗材、配件的获取难度

## 输出格式（JSON数组）：
```json
[
  {
    "user_scenario": "用户的使用场景描述",
    "product_spec": "相关的产品参数",
    "warning_message": "警告信息：为什么会撞墙",
    "impact_percentage": 性能下降百分比(0-100),
    "recommendation": "具体建议"
  }
]
```

## 注意事项
- 只输出有科学依据的警告，不要臆测
- impact_percentage 要基于物理/技术原理估算
- 建议要具体可行，不能只说"不建议购买"

如果场景信息不足或没有明显冲突，返回空数组 []"""


class ScenarioAgent(BaseAgent):
    """使用场景撞墙预测 Agent"""
    
    @property
    def name(self) -> str:
        return "场景撞墙预测"
    
    @property
    def description(self) -> str:
        return "基于使用场景预测产品可能出现的问题"
    
    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        执行场景预测分析
        
        Input:
            - product_name: 产品名称
            - product_specs: 产品参数（可选）
            - user_scenario: 用户使用场景描述
        
        Output:
            - warnings: 场景警告列表
        """
        product_name = input_data.get("product_name", "")
        product_specs = input_data.get("product_specs", "")
        user_scenario = input_data.get("user_scenario", "")
        
        if not user_scenario:
            # 没有场景描述时返回通用警告
            return self._get_demo_result(product_name)
        
        user_prompt = f"""
产品名称：{product_name}

产品参数：
{product_specs if product_specs else "（未提供详细参数，请基于该类产品的常见参数范围分析）"}

用户使用场景：
{user_scenario}

请分析这款产品在用户描述的场景下可能遇到的问题。
"""
        
        response = await self.call_llm(SCENARIO_SYSTEM_PROMPT, user_prompt)
        
        try:
            warnings_data = json.loads(response)
            warnings = [
                ScenarioWarning(
                    user_scenario=w["user_scenario"],
                    product_spec=w["product_spec"],
                    warning_message=w["warning_message"],
                    impact_percentage=w["impact_percentage"],
                    recommendation=w["recommendation"]
                )
                for w in warnings_data
            ]
        except (json.JSONDecodeError, KeyError, ValueError):
            warnings = []
        
        return {"warnings": warnings}
    
    def _get_demo_result(self, product_name: str) -> dict[str, Any]:
        """返回演示数据"""
        demo_warnings = {
            "扫地机器人": [
                ScenarioWarning(
                    user_scenario="家中有地毯和硬地板混合地面",
                    product_spec="吸力: 2700Pa, 地毯识别: 有",
                    warning_message="该款机器人的地毯增压功能在深色地毯上识别率仅60%，可能导致地毯区域清洁不彻底",
                    impact_percentage=40,
                    recommendation="建议在App中手动划定地毯区域，或选择带激光地毯识别的型号"
                ),
                ScenarioWarning(
                    user_scenario="家中有2cm以上门槛",
                    product_spec="越障高度: 2cm",
                    warning_message="标称越障高度为极限值，实际使用中1.8cm以上门槛就可能卡住",
                    impact_percentage=100,
                    recommendation="建议购买越障高度2.5cm以上的型号，或安装过门坡道"
                ),
                ScenarioWarning(
                    user_scenario="家中养宠物（猫/狗）",
                    product_spec="避障系统: 红外+超声波",
                    warning_message="该避障方案对宠物粪便识别率低，存在\"翻车\"风险",
                    impact_percentage=0,
                    recommendation="强烈建议选择带AI视觉识别的型号，或在无人时运行"
                )
            ],
            "投影仪": [
                ScenarioWarning(
                    user_scenario="客厅使用，白天有自然光",
                    product_spec="亮度: 2000 ANSI流明",
                    warning_message="在300lux以上环境光下，画面对比度下降约70%，白天几乎无法观看",
                    impact_percentage=70,
                    recommendation="建议选择3000流明以上的激光投影，或安装遮光窗帘"
                ),
                ScenarioWarning(
                    user_scenario="卧室使用，投射距离2米",
                    product_spec="投射比: 1.2:1",
                    warning_message="2米距离仅能投射约60英寸画面，可能小于预期",
                    impact_percentage=30,
                    recommendation="如需100英寸画面，投射距离需3.3米，建议考虑短焦机型"
                )
            ],
            "default": [
                ScenarioWarning(
                    user_scenario="日常高强度使用",
                    product_spec="设计使用寿命: 标准级",
                    warning_message="该产品定位为轻度使用场景，高强度使用可能加速损耗",
                    impact_percentage=30,
                    recommendation="建议选择商用级或专业级产品"
                )
            ]
        }
        
        for key in demo_warnings:
            if key in product_name:
                return {"warnings": demo_warnings[key]}
        
        return {"warnings": demo_warnings["default"]}
