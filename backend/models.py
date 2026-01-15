"""
The Last 5% - Data Models
数据模型定义
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime


class RiskLevel(str, Enum):
    """避坑风险等级"""
    SAFE = "safe"           # 可以一试
    CAUTION = "caution"     # 需要注意
    WARNING = "warning"     # 谨慎购买
    DANGER = "danger"       # 建议放弃
    RUN = "run"             # 快跑！


class DefectCategory(str, Enum):
    """缺陷类别"""
    HARDWARE = "hardware"       # 硬件故障
    SOFTWARE = "software"       # 软件Bug
    DESIGN = "design"           # 设计缺陷
    DURABILITY = "durability"   # 耐久性问题
    PERFORMANCE = "performance" # 性能不足
    SAFETY = "safety"           # 安全隐患
    VALUE = "value"             # 性价比问题


class ReviewSource(BaseModel):
    """评论来源"""
    platform: str = Field(..., description="来源平台")
    url: str = Field(..., description="原始链接")
    author: Optional[str] = Field(None, description="作者")
    date: Optional[datetime] = Field(None, description="发布日期")
    credibility_score: float = Field(0.5, ge=0, le=1, description="可信度评分")


class ExtractedDefect(BaseModel):
    """提取的缺陷"""
    category: DefectCategory = Field(..., description="缺陷类别")
    description: str = Field(..., description="缺陷描述")
    severity: int = Field(..., ge=1, le=10, description="严重程度 1-10")
    frequency: int = Field(1, description="被提及次数")
    sources: list[ReviewSource] = Field(default_factory=list, description="来源列表")
    original_quotes: list[str] = Field(default_factory=list, description="原始吐槽")


class ScenarioWarning(BaseModel):
    """场景撞墙警告"""
    user_scenario: str = Field(..., description="用户使用场景")
    product_spec: str = Field(..., description="相关产品参数")
    warning_message: str = Field(..., description="警告信息")
    impact_percentage: float = Field(..., description="性能影响百分比")
    recommendation: str = Field(..., description="建议")


class ProductHistory(BaseModel):
    """产品黑历史"""
    event_type: str = Field(..., description="事件类型: recall/defect/rebrand")
    event_date: Optional[str] = Field(None, description="事件日期")
    description: str = Field(..., description="事件描述")
    source_url: str = Field(..., description="信息来源")
    related_models: list[str] = Field(default_factory=list, description="相关型号")


class HeatmapData(BaseModel):
    """吐槽热力图数据"""
    dimension: str = Field(..., description="维度名称")
    complaint_count: int = Field(..., description="吐槽次数")
    severity_avg: float = Field(..., description="平均严重度")
    percentage: float = Field(..., description="占比")


class AlternativeProduct(BaseModel):
    """替代方案"""
    name: str = Field(..., description="产品名称")
    price_range: str = Field(..., description="价格区间")
    advantage: str = Field(..., description="相比被劝退产品的优势")
    solved_defects: list[str] = Field(..., description="解决了哪些缺陷")
    link: Optional[str] = Field(None, description="购买链接")


class AnalysisRequest(BaseModel):
    """分析请求"""
    product_name: str = Field(..., description="产品名称或链接")
    user_scenario: Optional[str] = Field(None, description="用户使用场景描述")
    budget: Optional[str] = Field(None, description="预算范围")
    priorities: list[str] = Field(default_factory=list, description="关注重点")


class AnalysisResponse(BaseModel):
    """完整分析响应"""
    product_name: str = Field(..., description="产品名称")
    risk_level: RiskLevel = Field(..., description="避坑指数")
    risk_score: int = Field(..., ge=0, le=100, description="风险评分 0-100")
    summary: str = Field(..., description="一句话总结")
    
    # Agent A: 差评脱水结果
    defects: list[ExtractedDefect] = Field(default_factory=list, description="提取的缺陷")
    noise_filtered: int = Field(0, description="过滤掉的垃圾评论数")
    
    # Agent B: 场景撞墙预测
    scenario_warnings: list[ScenarioWarning] = Field(default_factory=list, description="场景警告")
    
    # Agent C: 黑历史
    history_events: list[ProductHistory] = Field(default_factory=list, description="黑历史事件")
    
    # 可视化数据
    heatmap_data: list[HeatmapData] = Field(default_factory=list, description="热力图数据")
    
    # 替代方案
    alternatives: list[AlternativeProduct] = Field(default_factory=list, description="替代方案")
    
    # 元数据
    analyzed_reviews_count: int = Field(0, description="分析的评论总数")
    data_sources: list[str] = Field(default_factory=list, description="数据来源平台")
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="分析时间")
