"""
The Last 5% - LangChain Tools
自定义工具集：评论抓取、参数分析、历史搜索
"""

from typing import Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
import json


# ============================================
# Tool Input Schemas
# ============================================

class ReviewSearchInput(BaseModel):
    """评论搜索工具输入"""
    product_name: str = Field(description="产品名称")
    platform: str = Field(default="all", description="平台: smzdm/zhihu/jd/taobao/all")
    review_type: str = Field(default="negative", description="评论类型: negative/追评/all")
    limit: int = Field(default=50, description="获取数量上限")


class ProductSpecInput(BaseModel):
    """产品参数分析工具输入"""
    product_name: str = Field(description="产品名称或型号")
    spec_category: str = Field(default="all", description="参数类别: performance/durability/safety/all")


class HistorySearchInput(BaseModel):
    """历史记录搜索工具输入"""
    product_name: str = Field(description="产品名称")
    brand: Optional[str] = Field(default=None, description="品牌名称")
    search_type: str = Field(default="all", description="搜索类型: recall/defect/rebrand/all")


class ScenarioAnalysisInput(BaseModel):
    """场景分析工具输入"""
    product_name: str = Field(description="产品名称")
    user_scenario: str = Field(description="用户使用场景描述")
    product_specs: Optional[str] = Field(default=None, description="产品参数（可选）")


# ============================================
# Custom Tools
# ============================================

class ReviewSearchTool(BaseTool):
    """
    评论搜索工具
    从多个平台抓取产品评论，专注于负面评价
    """
    name: str = "review_search"
    description: str = """搜索产品评论工具。用于从什么值得买、知乎、京东、淘宝等平台获取产品评论。
    特别擅长获取负面评价和追评（使用一段时间后的真实反馈）。
    输入产品名称，返回原始评论列表。"""
    args_schema: Type[BaseModel] = ReviewSearchInput
    
    def _run(
        self,
        product_name: str,
        platform: str = "all",
        review_type: str = "negative",
        limit: int = 50,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """执行评论搜索"""
        # 模拟数据 - 实际应接入爬虫或API
        demo_reviews = self._get_demo_reviews(product_name)
        
        result = {
            "product_name": product_name,
            "platform": platform,
            "review_type": review_type,
            "total_found": len(demo_reviews),
            "reviews": demo_reviews[:limit]
        }
        return json.dumps(result, ensure_ascii=False)
    
    def _get_demo_reviews(self, product_name: str) -> list:
        """获取演示评论数据"""
        reviews_db = {
            "扫地机器人": [
                {"content": "边刷每天都要手动清理头发，太麻烦了，女生用户慎入", "source": "什么值得买", "type": "追评"},
                {"content": "用了半年电机开始有异响，嗡嗡的声音很大", "source": "京东", "type": "追评"},
                {"content": "建图功能在我家L型客厅完全不行，经常漏扫", "source": "知乎", "type": "负面"},
                {"content": "标称180分钟续航，实际最多120分钟，虚标严重", "source": "什么值得买", "type": "负面"},
                {"content": "尘盒密封圈才3个月就老化了，每次倒灰都漏", "source": "淘宝", "type": "追评"},
                {"content": "避障很蠢，家里养猫的千万别买，翻车过两次了", "source": "小红书", "type": "负面"},
                {"content": "拖地功能鸡肋，拖完地板还是脏的", "source": "京东", "type": "负面"},
                {"content": "APP经常连不上，智能家居联动形同虚设", "source": "知乎", "type": "负面"},
            ],
            "折叠屏手机": [
                {"content": "用了3个月折痕越来越明显，强迫症受不了", "source": "知乎", "type": "追评"},
                {"content": "铰链进灰后有异响，官方说是正常现象", "source": "什么值得买", "type": "负面"},
                {"content": "内屏贴膜不能自己换，官方换一次要500", "source": "小红书", "type": "负面"},
                {"content": "电池不耐用，一天要充两次电", "source": "京东", "type": "负面"},
                {"content": "外屏太小了，很多APP适配不好", "source": "淘宝", "type": "负面"},
            ],
            "空气炸锅": [
                {"content": "内胆涂层用了半年开始掉，不知道吃进去多少", "source": "什么值得买", "type": "追评"},
                {"content": "噪音很大，像直升机起飞一样", "source": "京东", "type": "负面"},
                {"content": "容量虚标，说5L实际放不了多少东西", "source": "淘宝", "type": "负面"},
                {"content": "油烟味很重，厨房小的话受不了", "source": "知乎", "type": "负面"},
            ],
        }
        
        for key in reviews_db:
            if key in product_name:
                return reviews_db[key]
        
        return [
            {"content": "质量一般，用了一段时间就出问题了", "source": "京东", "type": "追评"},
            {"content": "性价比不高，同价位有更好的选择", "source": "什么值得买", "type": "负面"},
        ]


class ProductSpecTool(BaseTool):
    """
    产品参数分析工具
    获取产品的技术规格并分析潜在问题
    """
    name: str = "product_spec_analysis"
    description: str = """产品参数分析工具。用于获取产品的详细技术规格，并分析参数中可能存在的问题。
    可以发现虚标、设计缺陷等技术层面的问题。
    输入产品名称，返回参数分析结果。"""
    args_schema: Type[BaseModel] = ProductSpecInput
    
    def _run(
        self,
        product_name: str,
        spec_category: str = "all",
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """执行参数分析"""
        specs = self._get_product_specs(product_name)
        
        result = {
            "product_name": product_name,
            "specs": specs,
            "potential_issues": self._analyze_specs(specs)
        }
        return json.dumps(result, ensure_ascii=False)
    
    def _get_product_specs(self, product_name: str) -> dict:
        """获取产品参数"""
        specs_db = {
            "扫地机器人": {
                "suction_power": "2700Pa",
                "battery": "5200mAh",
                "runtime": "180min (标称)",
                "noise": "65dB",
                "climbing": "2cm",
                "dustbin": "400ml",
                "water_tank": "200ml",
                "navigation": "LDS激光导航",
                "obstacle_avoidance": "红外+超声波"
            },
            "投影仪": {
                "brightness": "2000 ANSI流明",
                "resolution": "1080P",
                "throw_ratio": "1.2:1",
                "contrast": "1000:1",
                "noise": "32dB",
                "lamp_life": "30000小时"
            },
        }
        
        for key in specs_db:
            if key in product_name:
                return specs_db[key]
        return {"info": "暂无详细参数"}
    
    def _analyze_specs(self, specs: dict) -> list:
        """分析参数潜在问题"""
        issues = []
        
        if "runtime" in specs and "标称" in specs["runtime"]:
            issues.append("续航时间为标称值，实际使用通常会打7-8折")
        
        if "obstacle_avoidance" in specs:
            if "红外" in specs["obstacle_avoidance"] and "AI" not in specs["obstacle_avoidance"]:
                issues.append("避障方案较为基础，对小型障碍物和宠物粪便识别能力有限")
        
        if "climbing" in specs:
            climb = specs["climbing"].replace("cm", "")
            if float(climb) <= 2:
                issues.append(f"越障高度{climb}cm为极限值，实际使用建议门槛高度低于{float(climb)-0.2}cm")
        
        return issues


class HistorySearchTool(BaseTool):
    """
    黑历史搜索工具
    搜索产品/品牌的召回、缺陷、换壳等历史记录
    """
    name: str = "history_search"
    description: str = """产品黑历史搜索工具。用于查找产品或品牌的历史问题记录。
    包括：官方召回事件、已知批量缺陷、换壳重生（问题产品改款）、品牌负面历史等。
    输入产品名称和品牌，返回历史问题记录。"""
    args_schema: Type[BaseModel] = HistorySearchInput
    
    def _run(
        self,
        product_name: str,
        brand: Optional[str] = None,
        search_type: str = "all",
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """执行历史搜索"""
        history = self._search_history(product_name, brand)
        
        result = {
            "product_name": product_name,
            "brand": brand,
            "history_events": history
        }
        return json.dumps(result, ensure_ascii=False)
    
    def _search_history(self, product_name: str, brand: Optional[str]) -> list:
        """搜索历史记录"""
        history_db = {
            "扫地机器人": [
                {
                    "type": "defect",
                    "date": "2024-03",
                    "description": "多名用户反映该系列产品存在电池鼓包问题，部分批次电芯质量不稳定",
                    "source": "什么值得买社区讨论"
                },
                {
                    "type": "rebrand",
                    "date": "2023-08",
                    "description": "该型号疑似为上一代问题产品的改款，核心模组相同仅更换外壳",
                    "source": "V2EX拆解帖"
                }
            ],
            "折叠屏手机": [
                {
                    "type": "recall",
                    "date": "2024-01",
                    "description": "首批用户中约2%出现屏幕触控失灵，官方启动免费换屏服务",
                    "source": "官方售后公告"
                }
            ],
        }
        
        for key in history_db:
            if key in product_name:
                return history_db[key]
        
        return [{"type": "info", "description": "暂未发现重大历史问题", "source": "综合搜索"}]


class ScenarioAnalysisTool(BaseTool):
    """
    场景撞墙预测工具
    基于用户场景和产品参数预测使用问题
    """
    name: str = "scenario_analysis"
    description: str = """使用场景分析工具。根据用户描述的使用场景和产品参数，预测可能遇到的问题。
    例如：用户说"客厅采光好"，分析投影仪在该光照条件下的实际表现。
    输入产品名称和使用场景，返回场景匹配分析。"""
    args_schema: Type[BaseModel] = ScenarioAnalysisInput
    
    def _run(
        self,
        product_name: str,
        user_scenario: str,
        product_specs: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """执行场景分析"""
        warnings = self._analyze_scenario(product_name, user_scenario)
        
        result = {
            "product_name": product_name,
            "user_scenario": user_scenario,
            "warnings": warnings
        }
        return json.dumps(result, ensure_ascii=False)
    
    def _analyze_scenario(self, product_name: str, scenario: str) -> list:
        """分析场景匹配度"""
        warnings = []
        
        # 扫地机器人场景分析
        if "扫地机" in product_name:
            if "猫" in scenario or "狗" in scenario or "宠物" in scenario:
                warnings.append({
                    "scenario": "养宠物家庭",
                    "warning": "基础避障方案对宠物粪便识别率低，存在\"翻车\"风险",
                    "impact": 100,
                    "suggestion": "建议选择带AI视觉避障的型号，或在宠物不在时运行"
                })
            if "地毯" in scenario:
                warnings.append({
                    "scenario": "有地毯环境",
                    "warning": "深色地毯识别率约60%，可能导致地毯区域清洁不彻底",
                    "impact": 40,
                    "suggestion": "建议在APP中手动划定地毯区域"
                })
            if "门槛" in scenario or "高低差" in scenario:
                warnings.append({
                    "scenario": "有门槛/高低差",
                    "warning": "2cm越障为极限值，实际1.8cm以上就可能卡住",
                    "impact": 80,
                    "suggestion": "建议安装过门坡道或选择越障能力更强的型号"
                })
        
        # 投影仪场景分析
        if "投影" in product_name:
            if "白天" in scenario or "采光" in scenario or "阳光" in scenario:
                warnings.append({
                    "scenario": "白天/强光环境使用",
                    "warning": "2000流明在300lux以上环境光下，画面对比度下降约70%",
                    "impact": 70,
                    "suggestion": "建议选择3000流明以上激光投影，或安装遮光窗帘"
                })
        
        if not warnings:
            warnings.append({
                "scenario": "通用场景",
                "warning": "基于现有信息未发现明显场景冲突",
                "impact": 0,
                "suggestion": "建议补充更详细的使用场景描述"
            })
        
        return warnings


# ============================================
# Tool Registry
# ============================================

def get_all_tools() -> list[BaseTool]:
    """获取所有可用工具"""
    return [
        ReviewSearchTool(),
        ProductSpecTool(),
        HistorySearchTool(),
        ScenarioAnalysisTool()
    ]
