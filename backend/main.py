"""
The Last 5% - Main Application
杠精选品助手 - 主应用入口
使用 LangChain 增强版
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from typing import Optional
import os

from backend.models import (
    AnalysisRequest, 
    AnalysisResponse, 
    RiskLevel,
    HeatmapData,
    AlternativeProduct
)
from backend.config import get_settings

# 尝试导入 LangChain Agent，如果失败则使用旧版 Agent
try:
    from backend.langchain_agent import ProductAnalysisAgent, get_agent
    USE_LANGCHAIN = True
except ImportError:
    from backend.agents import DenoiseAgent, ScenarioAgent, HistoryAgent
    USE_LANGCHAIN = False
    print("⚠️ LangChain not available, falling back to basic agents")


# Agent instances
langchain_agent: Optional[ProductAnalysisAgent] = None
denoise_agent = None
scenario_agent = None
history_agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global langchain_agent, denoise_agent, scenario_agent, history_agent
    
    if USE_LANGCHAIN:
        # 使用 LangChain Agent
        langchain_agent = get_agent()
        print("✅ LangChain Agent initialized")
    else:
        # 使用旧版 Agent
        denoise_agent = DenoiseAgent()
        scenario_agent = ScenarioAgent()
        history_agent = HistoryAgent()
        print("✅ Basic Agents initialized")
    
    yield
    
    # Cleanup
    if not USE_LANGCHAIN:
        if denoise_agent:
            await denoise_agent.close()
        if scenario_agent:
            await scenario_agent.close()
        if history_agent:
            await history_agent.close()


app = FastAPI(
    title="The Last 5% - 杠精选品助手",
    description="AI驱动的产品避坑分析工具，专注于告诉你「为什么不该买」。使用 LangChain 构建智能 Agent 链路。",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# Legacy Helper Functions (for non-LangChain mode)
# ============================================

def calculate_risk_score(defects: list, warnings: list, history_events: list) -> tuple[int, RiskLevel]:
    """计算风险评分和等级"""
    score = 0
    
    for defect in defects:
        score += defect.severity * (defect.frequency / 10)
    
    for warning in warnings:
        score += warning.impact_percentage * 0.3
    
    for event in history_events:
        if event.event_type == "recall":
            score += 20
        elif event.event_type == "defect":
            score += 15
        elif event.event_type == "rebrand":
            score += 10
        else:
            score += 5
    
    score = min(100, int(score))
    
    if score < 20:
        level = RiskLevel.SAFE
    elif score < 40:
        level = RiskLevel.CAUTION
    elif score < 60:
        level = RiskLevel.WARNING
    elif score < 80:
        level = RiskLevel.DANGER
    else:
        level = RiskLevel.RUN
    
    return score, level


def generate_heatmap_data(defects: list) -> list[HeatmapData]:
    """生成吐槽热力图数据"""
    category_stats = {}
    total_frequency = 0
    
    for defect in defects:
        cat = defect.category.value
        if cat not in category_stats:
            category_stats[cat] = {"count": 0, "severity_sum": 0}
        category_stats[cat]["count"] += defect.frequency
        category_stats[cat]["severity_sum"] += defect.severity * defect.frequency
        total_frequency += defect.frequency
    
    heatmap = []
    category_names = {
        "hardware": "硬件故障", "software": "软件Bug", "design": "设计缺陷",
        "durability": "耐久性", "performance": "性能问题", "safety": "安全隐患", "value": "性价比"
    }
    
    for cat, stats in category_stats.items():
        heatmap.append(HeatmapData(
            dimension=category_names.get(cat, cat),
            complaint_count=stats["count"],
            severity_avg=round(stats["severity_sum"] / stats["count"], 1) if stats["count"] > 0 else 0,
            percentage=round(stats["count"] / total_frequency * 100, 1) if total_frequency > 0 else 0
        ))
    
    heatmap.sort(key=lambda x: x.complaint_count, reverse=True)
    return heatmap


def generate_alternatives(product_name: str, defects: list) -> list[AlternativeProduct]:
    """生成替代方案建议"""
    alternatives_db = {
        "扫地机器人": [
            AlternativeProduct(name="石头 G20", price_range="3000-3500元",
                advantage="全自动洗拖布，彻底解决边刷缠绕问题", solved_defects=["边刷缠绕", "清洁效果"], link=None),
            AlternativeProduct(name="追觅 S10 Pro", price_range="2500-3000元",
                advantage="AI视觉避障，不会误触宠物粪便", solved_defects=["避障能力", "建图准确性"], link=None),
            AlternativeProduct(name="云鲸 J4", price_range="3500-4000元",
                advantage="分体式设计，维护简单，电机5年质保", solved_defects=["电机耐久性", "维护成本"], link=None)
        ],
        "default": [
            AlternativeProduct(name="同类竞品 A", price_range="相近价位",
                advantage="解决了主要吐槽问题", solved_defects=["核心缺陷"], link=None)
        ]
    }
    
    for key in alternatives_db:
        if key in product_name:
            return alternatives_db[key]
    return alternatives_db["default"]


def generate_summary(product_name: str, risk_level: RiskLevel, defects: list) -> str:
    """生成一句话总结"""
    summaries = {
        RiskLevel.SAFE: f"「{product_name}」整体表现良好，未发现重大硬伤，可以放心购买。",
        RiskLevel.CAUTION: f"「{product_name}」存在一些小问题，但不影响核心功能，购买前请了解清楚。",
        RiskLevel.WARNING: f"「{product_name}」有明显短板，建议对比同类竞品后再决定。",
        RiskLevel.DANGER: f"「{product_name}」问题较多，非刚需不建议购买，建议看看替代方案。",
        RiskLevel.RUN: f"「{product_name}」存在严重问题，强烈建议放弃，换一个吧！"
    }
    
    base_summary = summaries.get(risk_level, "")
    if defects:
        top_defect = max(defects, key=lambda x: x.severity * x.frequency)
        base_summary += f" 最大槽点：{top_defect.description}"
    return base_summary


# ============================================
# API Routes
# ============================================

@app.get("/")
async def root():
    """Serve the frontend"""
    return FileResponse("frontend/index.html")


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_product(request: AnalysisRequest):
    """
    分析产品，返回避坑报告
    
    使用 LangChain Agent 进行深度分析：
    1. 评论搜索工具 - 获取全网真实评价
    2. 参数分析工具 - 发现技术层面问题
    3. 历史搜索工具 - 挖掘召回/缺陷等黑历史
    4. 场景分析工具 - 基于使用场景预测问题
    """
    product_name = request.product_name
    user_scenario = request.user_scenario
    
    if USE_LANGCHAIN and langchain_agent:
        # 使用 LangChain Agent
        return await langchain_agent.analyze(product_name, user_scenario)
    
    # Fallback: 使用旧版 Agent
    if not denoise_agent or not scenario_agent or not history_agent:
        raise HTTPException(status_code=500, detail="Agents not initialized")
    
    import asyncio
    
    denoise_task = denoise_agent.execute({"product_name": product_name, "reviews": []})
    scenario_task = scenario_agent.execute({"product_name": product_name, "user_scenario": user_scenario or ""})
    history_task = history_agent.execute({"product_name": product_name})
    
    denoise_result, scenario_result, history_result = await asyncio.gather(
        denoise_task, scenario_task, history_task
    )
    
    defects = denoise_result.get("defects", [])
    noise_filtered = denoise_result.get("noise_filtered", 0)
    warnings = scenario_result.get("warnings", [])
    history_events = history_result.get("history_events", [])
    
    risk_score, risk_level = calculate_risk_score(defects, warnings, history_events)
    heatmap_data = generate_heatmap_data(defects)
    alternatives = generate_alternatives(product_name, defects)
    summary = generate_summary(product_name, risk_level, defects)
    
    return AnalysisResponse(
        product_name=product_name,
        risk_level=risk_level,
        risk_score=risk_score,
        summary=summary,
        defects=defects,
        noise_filtered=noise_filtered,
        scenario_warnings=warnings,
        history_events=history_events,
        heatmap_data=heatmap_data,
        alternatives=alternatives,
        analyzed_reviews_count=noise_filtered + sum(d.frequency for d in defects),
        data_sources=["什么值得买", "知乎", "B站", "V2EX", "京东", "淘宝"]
    )


@app.post("/api/chat")
async def chat(request: dict):
    """
    对话式交互 API
    支持多轮对话，记住上下文
    """
    if not USE_LANGCHAIN or not langchain_agent:
        return {"error": "Chat requires LangChain", "message": "请使用 /api/analyze 端点"}
    
    message = request.get("message", "")
    if not message:
        return {"error": "Message required"}
    
    # 简单场景：如果消息包含产品名称，进行分析
    # 复杂场景可以扩展为真正的对话
    return await langchain_agent.analyze(message)


@app.get("/api/health")
async def health_check():
    """健康检查"""
    settings = get_settings()
    return {
        "status": "healthy",
        "version": "2.0.0",
        "langchain_enabled": USE_LANGCHAIN,
        "llm_provider": settings.llm_provider,
        "agents": {
            "langchain_agent": langchain_agent is not None,
            "denoise": denoise_agent is not None if not USE_LANGCHAIN else None,
            "scenario": scenario_agent is not None if not USE_LANGCHAIN else None,
            "history": history_agent is not None if not USE_LANGCHAIN else None
        }
    }


@app.get("/api/tools")
async def list_tools():
    """列出所有可用工具"""
    if USE_LANGCHAIN:
        from backend.langchain_tools import get_all_tools
        tools = get_all_tools()
        return {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description
                }
                for tool in tools
            ]
        }
    return {"tools": [], "message": "LangChain not enabled"}


# Mount static files
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
