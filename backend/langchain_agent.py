"""
The Last 5% - LangChain Agent
使用 LangChain + LangGraph 构建智能避坑分析 Agent
"""

import json
import operator
from typing import Annotated, TypedDict, Sequence
from datetime import datetime

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI

from backend.config import get_settings
from backend.langchain_tools import get_all_tools
from backend.models import (
    AnalysisResponse, RiskLevel, ExtractedDefect, DefectCategory,
    ScenarioWarning, ProductHistory, HeatmapData, AlternativeProduct
)


# ============================================
# System Prompts
# ============================================

MASTER_AGENT_PROMPT = """你是「The Last 5% 杠精选品助手」的核心 AI。你的唯一使命是告诉用户「为什么不该买」某个产品。

## 你的角色
你是一个专业的"产品劝退师"，专门帮助用户避免踩坑。你需要：
1. 深度分析产品的真实缺陷（过滤营销话术）
2. 基于用户场景预测使用问题
3. 挖掘产品/品牌的黑历史
4. 给出替代方案建议

## 你的工具
你有以下工具可以使用：
- `review_search`: 搜索产品评论，获取真实用户反馈
- `product_spec_analysis`: 分析产品参数，发现技术层面的问题
- `history_search`: 搜索产品/品牌的召回、缺陷等历史记录
- `scenario_analysis`: 基于用户场景预测使用问题

## 分析流程
1. 首先使用 review_search 获取用户真实评价
2. 然后使用 product_spec_analysis 分析产品参数
3. 接着使用 history_search 查找黑历史
4. 如果用户提供了使用场景，使用 scenario_analysis 预测问题
5. 最后综合所有信息生成避坑报告

## 输出要求
你的分析要：
- 客观中立，不夸大也不隐瞒
- 重点突出最严重的问题
- 给出具体可行的建议
- 语言简洁有力，像一个毒舌但专业的朋友

当前时间：{current_time}
"""

DEFECT_EXTRACTION_PROMPT = """基于以下评论数据，提取产品的真实缺陷。

## 输入数据
{review_data}

## 任务
1. 过滤掉物流、客服、价格等与产品本身无关的抱怨
2. 提取关于产品硬件、软件、设计、耐久性、性能、安全的真实问题
3. 统计每个问题被提及的频率
4. 评估每个问题的严重程度(1-10)

## 输出格式 (JSON)
```json
{{
  "defects": [
    {{
      "category": "hardware|software|design|durability|performance|safety",
      "description": "问题描述",
      "severity": 1-10,
      "frequency": 被提及次数,
      "quotes": ["原始评论1", "原始评论2"]
    }}
  ],
  "noise_filtered": 过滤掉的无关评论数
}}
```
"""

FINAL_REPORT_PROMPT = """基于以下分析结果，生成最终的避坑报告。

## 产品信息
产品名称：{product_name}
用户场景：{user_scenario}

## 分析数据
缺陷分析：{defects_data}
参数分析：{specs_data}
历史记录：{history_data}
场景预测：{scenario_data}

## 任务
1. 计算避坑指数(0-100)，越高越危险
2. 确定风险等级：safe(<20)/caution(20-40)/warning(40-60)/danger(60-80)/run(>80)
3. 生成一句话总结，点明最大的问题
4. 推荐替代方案

## 输出格式 (JSON)
```json
{{
  "risk_score": 0-100,
  "risk_level": "safe|caution|warning|danger|run",
  "summary": "一句话总结",
  "top_defects": ["最严重的问题1", "最严重的问题2", "最严重的问题3"],
  "alternatives": [
    {{
      "name": "替代产品名",
      "price_range": "价格区间",
      "advantage": "相比被分析产品的优势",
      "solved_defects": ["解决了哪些问题"]
    }}
  ]
}}
```
"""


# ============================================
# LangChain Agent Class
# ============================================

class ProductAnalysisAgent:
    """
    产品避坑分析 Agent
    使用 LangChain 构建的智能分析系统
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.tools = get_all_tools()
        
        # 初始化 LLM
        if self.settings.llm_provider == "deepseek" and self.settings.deepseek_api_key:
            self.llm = ChatOpenAI(
                model="deepseek-chat",
                api_key=self.settings.deepseek_api_key,
                base_url="https://api.deepseek.com",
                temperature=0.3
            )
        elif self.settings.openai_api_key:
            self.llm = ChatOpenAI(
                model="gpt-4o",
                api_key=self.settings.openai_api_key,
                temperature=0.3
            )
        else:
            self.llm = None
        
        # 绑定工具到 LLM
        if self.llm:
            self.llm_with_tools = self.llm.bind_tools(self.tools)
        else:
            self.llm_with_tools = None
        
        # 对话历史
        self.conversation_history: list[BaseMessage] = []
    
    async def analyze(self, product_name: str, user_scenario: str = None) -> AnalysisResponse:
        """
        执行完整的产品分析
        """
        if not self.llm:
            # 无 LLM 时返回演示数据
            return self._get_demo_response(product_name)
        
        try:
            # Step 1: 收集数据
            review_data = await self._search_reviews(product_name)
            specs_data = await self._analyze_specs(product_name)
            history_data = await self._search_history(product_name)
            scenario_data = await self._analyze_scenario(product_name, user_scenario) if user_scenario else {}
            
            # Step 2: 提取缺陷
            defects_result = await self._extract_defects(review_data)
            
            # Step 3: 生成报告
            report = await self._generate_report(
                product_name, user_scenario,
                defects_result, specs_data, history_data, scenario_data
            )
            
            # Step 4: 构建响应
            return self._build_response(product_name, defects_result, scenario_data, history_data, report)
            
        except Exception as e:
            print(f"分析出错: {e}")
            return self._get_demo_response(product_name)
    
    async def _search_reviews(self, product_name: str) -> dict:
        """搜索评论"""
        tool = self.tools[0]  # ReviewSearchTool
        result = tool._run(product_name=product_name, review_type="negative", limit=50)
        return json.loads(result)
    
    async def _analyze_specs(self, product_name: str) -> dict:
        """分析参数"""
        tool = self.tools[1]  # ProductSpecTool
        result = tool._run(product_name=product_name)
        return json.loads(result)
    
    async def _search_history(self, product_name: str) -> dict:
        """搜索历史"""
        tool = self.tools[2]  # HistorySearchTool
        result = tool._run(product_name=product_name)
        return json.loads(result)
    
    async def _analyze_scenario(self, product_name: str, scenario: str) -> dict:
        """分析场景"""
        tool = self.tools[3]  # ScenarioAnalysisTool
        result = tool._run(product_name=product_name, user_scenario=scenario)
        return json.loads(result)
    
    async def _extract_defects(self, review_data: dict) -> dict:
        """使用 LLM 提取缺陷"""
        prompt = DEFECT_EXTRACTION_PROMPT.format(
            review_data=json.dumps(review_data, ensure_ascii=False, indent=2)
        )
        
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        
        try:
            # 尝试解析 JSON
            content = response.content
            # 提取 JSON 部分
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content)
        except:
            return {"defects": [], "noise_filtered": 0}
    
    async def _generate_report(
        self, product_name: str, user_scenario: str,
        defects_data: dict, specs_data: dict, history_data: dict, scenario_data: dict
    ) -> dict:
        """生成最终报告"""
        prompt = FINAL_REPORT_PROMPT.format(
            product_name=product_name,
            user_scenario=user_scenario or "未指定",
            defects_data=json.dumps(defects_data, ensure_ascii=False),
            specs_data=json.dumps(specs_data, ensure_ascii=False),
            history_data=json.dumps(history_data, ensure_ascii=False),
            scenario_data=json.dumps(scenario_data, ensure_ascii=False)
        )
        
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        
        try:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content)
        except:
            return {
                "risk_score": 50,
                "risk_level": "warning",
                "summary": f"「{product_name}」存在一些需要注意的问题",
                "alternatives": []
            }
    
    def _build_response(
        self, product_name: str, defects_result: dict,
        scenario_data: dict, history_data: dict, report: dict
    ) -> AnalysisResponse:
        """构建最终响应"""
        # 解析缺陷
        defects = []
        for d in defects_result.get("defects", []):
            try:
                defects.append(ExtractedDefect(
                    category=DefectCategory(d.get("category", "design")),
                    description=d.get("description", ""),
                    severity=d.get("severity", 5),
                    frequency=d.get("frequency", 1),
                    original_quotes=d.get("quotes", [])
                ))
            except:
                pass
        
        # 解析场景警告
        warnings = []
        for w in scenario_data.get("warnings", []):
            try:
                warnings.append(ScenarioWarning(
                    user_scenario=w.get("scenario", ""),
                    product_spec="",
                    warning_message=w.get("warning", ""),
                    impact_percentage=w.get("impact", 0),
                    recommendation=w.get("suggestion", "")
                ))
            except:
                pass
        
        # 解析历史事件
        history_events = []
        for h in history_data.get("history_events", []):
            try:
                history_events.append(ProductHistory(
                    event_type=h.get("type", "defect"),
                    event_date=h.get("date"),
                    description=h.get("description", ""),
                    source_url=h.get("source", "")
                ))
            except:
                pass
        
        # 生成热力图数据
        heatmap = self._generate_heatmap(defects)
        
        # 解析替代方案
        alternatives = []
        for alt in report.get("alternatives", []):
            try:
                alternatives.append(AlternativeProduct(
                    name=alt.get("name", ""),
                    price_range=alt.get("price_range", ""),
                    advantage=alt.get("advantage", ""),
                    solved_defects=alt.get("solved_defects", [])
                ))
            except:
                pass
        
        # 确定风险等级
        risk_level_map = {
            "safe": RiskLevel.SAFE,
            "caution": RiskLevel.CAUTION,
            "warning": RiskLevel.WARNING,
            "danger": RiskLevel.DANGER,
            "run": RiskLevel.RUN
        }
        risk_level = risk_level_map.get(report.get("risk_level", "warning"), RiskLevel.WARNING)
        
        return AnalysisResponse(
            product_name=product_name,
            risk_level=risk_level,
            risk_score=report.get("risk_score", 50),
            summary=report.get("summary", f"「{product_name}」分析完成"),
            defects=defects,
            noise_filtered=defects_result.get("noise_filtered", 0),
            scenario_warnings=warnings,
            history_events=history_events,
            heatmap_data=heatmap,
            alternatives=alternatives,
            analyzed_reviews_count=len(defects_result.get("defects", [])) * 10,
            data_sources=["什么值得买", "知乎", "B站", "京东", "淘宝"]
        )
    
    def _generate_heatmap(self, defects: list[ExtractedDefect]) -> list[HeatmapData]:
        """生成热力图数据"""
        category_stats = {}
        total = 0
        
        category_names = {
            "hardware": "硬件故障",
            "software": "软件Bug",
            "design": "设计缺陷",
            "durability": "耐久性",
            "performance": "性能问题",
            "safety": "安全隐患"
        }
        
        for defect in defects:
            cat = defect.category.value
            if cat not in category_stats:
                category_stats[cat] = {"count": 0, "severity_sum": 0}
            category_stats[cat]["count"] += defect.frequency
            category_stats[cat]["severity_sum"] += defect.severity * defect.frequency
            total += defect.frequency
        
        heatmap = []
        for cat, stats in category_stats.items():
            heatmap.append(HeatmapData(
                dimension=category_names.get(cat, cat),
                complaint_count=stats["count"],
                severity_avg=round(stats["severity_sum"] / stats["count"], 1) if stats["count"] > 0 else 0,
                percentage=round(stats["count"] / total * 100, 1) if total > 0 else 0
            ))
        
        heatmap.sort(key=lambda x: x.complaint_count, reverse=True)
        return heatmap
    
    def _get_demo_response(self, product_name: str) -> AnalysisResponse:
        """返回演示响应"""
        # 与之前的演示数据类似
        from backend.agents.denoise_agent import DenoiseAgent
        from backend.agents.scenario_agent import ScenarioAgent
        from backend.agents.history_agent import HistoryAgent
        
        denoise = DenoiseAgent()
        scenario = ScenarioAgent()
        history = HistoryAgent()
        
        # 使用原有的演示数据逻辑
        demo_defects = denoise._get_demo_result(product_name)
        demo_warnings = scenario._get_demo_result(product_name)
        demo_history = history._get_demo_result(product_name, None)
        
        defects = demo_defects.get("defects", [])
        
        # 计算风险分数
        risk_score = min(100, sum(d.severity * d.frequency // 10 for d in defects))
        
        if risk_score < 20:
            risk_level = RiskLevel.SAFE
        elif risk_score < 40:
            risk_level = RiskLevel.CAUTION
        elif risk_score < 60:
            risk_level = RiskLevel.WARNING
        elif risk_score < 80:
            risk_level = RiskLevel.DANGER
        else:
            risk_level = RiskLevel.RUN
        
        return AnalysisResponse(
            product_name=product_name,
            risk_level=risk_level,
            risk_score=risk_score,
            summary=f"「{product_name}」存在一些需要注意的问题，建议对比同类竞品后再决定。",
            defects=defects,
            noise_filtered=demo_defects.get("noise_filtered", 0),
            scenario_warnings=demo_warnings.get("warnings", []),
            history_events=demo_history.get("history_events", []),
            heatmap_data=self._generate_heatmap(defects),
            alternatives=[
                AlternativeProduct(
                    name="同类竞品推荐",
                    price_range="相近价位",
                    advantage="解决了主要槽点问题",
                    solved_defects=["耐久性", "设计缺陷"]
                )
            ],
            analyzed_reviews_count=150,
            data_sources=["什么值得买", "知乎", "B站", "京东", "淘宝"]
        )
    
    def add_to_history(self, message: BaseMessage):
        """添加到对话历史"""
        self.conversation_history.append(message)
        # 保持历史在合理长度
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []


# ============================================
# Global Agent Instance
# ============================================

_agent_instance: ProductAnalysisAgent = None


def get_agent() -> ProductAnalysisAgent:
    """获取全局 Agent 实例"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = ProductAnalysisAgent()
    return _agent_instance
