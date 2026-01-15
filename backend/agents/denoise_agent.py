"""
The Last 5% - Agent A: 差评脱水机 (De-noise Agent)
自动过滤垃圾信息，只提取关于产品本身的硬件故障、软件Bug或设计缺陷
"""

import json
from typing import Any
from backend.agents.base_agent import BaseAgent
from backend.models import ExtractedDefect, DefectCategory, ReviewSource


DENOISE_SYSTEM_PROMPT = """你是一个专业的差评分析专家，专门从海量用户评论中提取真实有价值的产品缺陷信息。

## 你的任务
从用户评论中识别并提取**真正的产品问题**，过滤掉无关噪音。

## 需要过滤的"噪音"类型（直接忽略）：
1. 物流相关："发货慢"、"快递破损"、"送错地址"
2. 客服相关："客服态度差"、"退款慢"、"不给换货"
3. 纯情绪宣泄："垃圾"、"再也不买了"、"骗子"（无具体问题描述）
4. 主观偏好："颜色不喜欢"、"比想象的大/小"
5. 价格波动："买贵了"、"降价了没补差"
6. 虚假好评的反向："明显刷单"、"评论都是假的"

## 需要提取的"真实缺陷"类型：
1. **硬件故障** (hardware)：部件损坏、异响、漏电、发热异常
2. **软件Bug** (software)：系统卡顿、APP闪退、固件问题
3. **设计缺陷** (design)：结构不合理、使用不便、人体工学问题
4. **耐久性问题** (durability)：材质老化、涂层脱落、使用X月后出问题
5. **性能不足** (performance)：参数虚标、实际效果差、功率不足
6. **安全隐患** (safety)：过热、漏电、材料有害

## 输出格式（JSON数组）：
```json
[
  {
    "category": "hardware|software|design|durability|performance|safety",
    "description": "简洁描述这个缺陷是什么",
    "severity": 1-10的严重程度评分,
    "frequency": 在提供的评论中被提及的次数,
    "original_quotes": ["原始评论摘录1", "原始评论摘录2"]
  }
]
```

## 严重程度评分标准：
- 1-3：小问题，不影响核心功能
- 4-6：中等问题，影响使用体验
- 7-8：严重问题，影响核心功能
- 9-10：致命问题，安全隐患或产品基本不可用

如果没有发现任何真实缺陷，返回空数组 []"""


class DenoiseAgent(BaseAgent):
    """差评脱水机 Agent"""
    
    @property
    def name(self) -> str:
        return "差评脱水机"
    
    @property
    def description(self) -> str:
        return "过滤垃圾评论，提取真实产品缺陷"
    
    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        执行差评脱水分析
        
        Input:
            - product_name: 产品名称
            - reviews: 原始评论列表
        
        Output:
            - defects: 提取的缺陷列表
            - noise_filtered: 过滤的噪音数量
        """
        product_name = input_data.get("product_name", "")
        reviews = input_data.get("reviews", [])
        
        if not reviews:
            # 使用模拟数据进行演示
            return self._get_demo_result(product_name)
        
        # 构建用户提示
        reviews_text = "\n".join([f"- {r}" for r in reviews[:100]])  # 限制100条
        user_prompt = f"""
产品名称：{product_name}

以下是收集到的用户评论（共{len(reviews)}条）：

{reviews_text}

请分析这些评论，提取真实的产品缺陷。
"""
        
        # 调用 LLM
        response = await self.call_llm(DENOISE_SYSTEM_PROMPT, user_prompt)
        
        try:
            defects_data = json.loads(response)
            defects = [
                ExtractedDefect(
                    category=DefectCategory(d["category"]),
                    description=d["description"],
                    severity=d["severity"],
                    frequency=d.get("frequency", 1),
                    original_quotes=d.get("original_quotes", [])
                )
                for d in defects_data
            ]
        except (json.JSONDecodeError, KeyError, ValueError):
            defects = []
        
        # 计算过滤的噪音数量
        total_issues_mentioned = sum(d.frequency for d in defects)
        noise_filtered = max(0, len(reviews) - total_issues_mentioned)
        
        return {
            "defects": defects,
            "noise_filtered": noise_filtered
        }
    
    def _get_demo_result(self, product_name: str) -> dict[str, Any]:
        """返回演示数据"""
        # 根据产品名称返回不同的模拟数据
        demo_defects = {
            "扫地机器人": [
                ExtractedDefect(
                    category=DefectCategory.DESIGN,
                    description="边刷容易缠绕头发，清理困难",
                    severity=6,
                    frequency=47,
                    original_quotes=[
                        "边刷每天都要手动清理头发，太麻烦了",
                        "女生用户慎入，头发缠绕问题严重",
                        "用了一个月，边刷已经被头发缠死了"
                    ]
                ),
                ExtractedDefect(
                    category=DefectCategory.SOFTWARE,
                    description="建图功能在复杂户型下经常出错，重复清扫或漏扫",
                    severity=7,
                    frequency=32,
                    original_quotes=[
                        "家里有个L型拐角，每次都识别不出来",
                        "建图建了三次都不对，客厅直接漏掉",
                        "地图经常莫名其妙重置"
                    ]
                ),
                ExtractedDefect(
                    category=DefectCategory.HARDWARE,
                    description="使用6个月后主刷电机异响明显",
                    severity=8,
                    frequency=28,
                    original_quotes=[
                        "半年后开始有很大的嗡嗡声",
                        "电机声音越来越大，像拖拉机",
                        "过保后电机就出问题，维修费比新机还贵"
                    ]
                ),
                ExtractedDefect(
                    category=DefectCategory.DURABILITY,
                    description="尘盒密封圈老化快，3个月后漏灰",
                    severity=5,
                    frequency=19,
                    original_quotes=[
                        "尘盒盖子关不紧了，每次倒灰弄一手",
                        "密封条才用几个月就变形了"
                    ]
                ),
                ExtractedDefect(
                    category=DefectCategory.PERFORMANCE,
                    description="实际续航比标称短30%，大户型无法一次清扫完",
                    severity=6,
                    frequency=24,
                    original_quotes=[
                        "说好的180分钟，实际只有120分钟",
                        "100平的房子要充两次电才能扫完",
                        "吸力开到最大，续航直接减半"
                    ]
                )
            ],
            "default": [
                ExtractedDefect(
                    category=DefectCategory.DESIGN,
                    description="人体工学设计不合理，长时间使用不适",
                    severity=6,
                    frequency=15,
                    original_quotes=["用久了很累", "设计反人类"]
                ),
                ExtractedDefect(
                    category=DefectCategory.DURABILITY,
                    description="材质耐久性差，使用3个月后明显老化",
                    severity=7,
                    frequency=23,
                    original_quotes=["才用3个月就坏了", "质量堪忧"]
                )
            ]
        }
        
        # 匹配产品关键词
        for key in demo_defects:
            if key in product_name:
                return {
                    "defects": demo_defects[key],
                    "noise_filtered": 156
                }
        
        return {
            "defects": demo_defects["default"],
            "noise_filtered": 89
        }
