"""
The Last 5% - Agent C: 全网黑历史追溯 (History Agent)
追溯产品/品牌的历史问题、召回事件、换壳前身等
"""

import json
from typing import Any
from backend.agents.base_agent import BaseAgent
from backend.models import ProductHistory


HISTORY_SYSTEM_PROMPT = """你是一个产品历史调查专家，专门挖掘产品和品牌的"黑历史"。

## 你的任务
调查并整理该产品/品牌的历史问题，包括：

1. **召回事件** (recall)
   - 官方召回公告
   - 质量问题导致的批量退换

2. **已知缺陷** (defect)
   - 被媒体曝光的质量问题
   - 集体投诉事件
   - 监管部门通报

3. **换壳重生** (rebrand)
   - 该产品是否是某款问题产品的改款
   - 换汤不换药的"新品"
   - ODM公模贴牌

4. **品牌历史** (brand_history)
   - 品牌过往的质量事故
   - 售后服务黑历史
   - 虚假宣传处罚

## 输出格式（JSON数组）：
```json
[
  {
    "event_type": "recall|defect|rebrand|brand_history",
    "event_date": "YYYY-MM 或 YYYY 或 null",
    "description": "事件描述",
    "source_url": "信息来源（可以是大致描述）",
    "related_models": ["相关型号1", "相关型号2"]
  }
]
```

## 注意事项
- 只输出有据可查的信息
- 优先输出近3年内的事件
- 如果是推测性信息，需要明确标注

如果没有查到任何黑历史，返回空数组 []"""


class HistoryAgent(BaseAgent):
    """全网黑历史追溯 Agent"""
    
    @property
    def name(self) -> str:
        return "黑历史追溯"
    
    @property
    def description(self) -> str:
        return "追溯产品和品牌的历史问题"
    
    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        执行黑历史追溯
        
        Input:
            - product_name: 产品名称
            - brand: 品牌名称（可选）
        
        Output:
            - history_events: 历史事件列表
        """
        product_name = input_data.get("product_name", "")
        brand = input_data.get("brand", "")
        
        # 在实际应用中，这里会调用搜索API或爬虫获取信息
        # 演示模式下返回模拟数据
        return self._get_demo_result(product_name, brand)
    
    def _get_demo_result(self, product_name: str, brand: str) -> dict[str, Any]:
        """返回演示数据"""
        demo_histories = {
            "扫地机器人": [
                ProductHistory(
                    event_type="defect",
                    event_date="2024-03",
                    description="多名用户反映该系列产品存在电池鼓包问题，品牌方承认部分批次电芯供应商质量不稳定",
                    source_url="什么值得买 - 扫地机器人避坑讨论帖",
                    related_models=["X10 Pro", "X10 Plus"]
                ),
                ProductHistory(
                    event_type="rebrand",
                    event_date="2023-08",
                    description="该型号实际为上一代「清洁专家S9」的改款，核心清洁模组相同，仅更换外壳和App界面",
                    source_url="V2EX - 扫地机器人拆解对比帖",
                    related_models=["清洁专家S9", "清洁专家S9 Max"]
                ),
                ProductHistory(
                    event_type="brand_history",
                    event_date="2022-11",
                    description="该品牌曾因虚标产品吸力参数被市场监管局约谈，后修改宣传页面",
                    source_url="国家市场监督管理总局公示",
                    related_models=[]
                )
            ],
            "折叠屏手机": [
                ProductHistory(
                    event_type="recall",
                    event_date="2024-01",
                    description="首批用户中约2%出现屏幕折痕加深、触控失灵问题，官方启动免费换屏服务",
                    source_url="品牌官方售后公告",
                    related_models=["Fold 5", "Fold 5 Pro"]
                ),
                ProductHistory(
                    event_type="defect",
                    event_date="2023-12",
                    description="多名用户反映铰链处进灰后出现异响，官方称\"属于正常现象\"引发争议",
                    source_url="知乎 - 折叠屏手机真实使用体验",
                    related_models=[]
                )
            ],
            "空气炸锅": [
                ProductHistory(
                    event_type="defect",
                    event_date="2024-05",
                    description="该型号内胆涂层被检测出PFOA含量超标，长期使用可能存在健康风险",
                    source_url="消费者协会抽检报告",
                    related_models=["AF-200", "AF-200 Pro"]
                ),
                ProductHistory(
                    event_type="brand_history",
                    event_date="2023-06",
                    description="品牌曾因产品说明书未标注正确的使用功率被通报",
                    source_url="市场监管总局通报",
                    related_models=[]
                )
            ],
            "default": [
                ProductHistory(
                    event_type="brand_history",
                    event_date="2023",
                    description="暂未发现该产品/品牌的重大负面历史记录。但建议关注最新用户反馈。",
                    source_url="综合搜索结果",
                    related_models=[]
                )
            ]
        }
        
        for key in demo_histories:
            if key in product_name:
                return {"history_events": demo_histories[key]}
        
        return {"history_events": demo_histories["default"]}
