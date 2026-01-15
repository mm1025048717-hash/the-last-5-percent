# The Last 5% - 杠精选品助手 ⚠️

> **专注于告诉你「为什么不该买」的 AI 选品工具**

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🎯 项目定位

在 AI + 电商领域，所有的选品工具都在努力告诉你「为什么要买」。

**The Last 5%** 的唯一使命是告诉你「**为什么不该买**」。

### 为什么这个点没人做？

- **大厂不敢做**：阿里、京东、亚马逊的底层逻辑是促成交易，他们不可能开发一个深度"劝退"工具
- **信息不对称**：普通用户看好评看的是营销，看差评看到的是情绪，很难看到「由于产品设计缺陷导致的必然失败」

## ✨ 核心功能

### 🔬 Agent A: 差评脱水机 (De-noise)

自动过滤「物流慢」「客服态度差」等垃圾信息，只提取关于产品本身的：
- 硬件故障
- 软件 Bug
- 设计缺陷
- 耐久性问题
- 性能不足
- 安全隐患

### ⚡ Agent B: 使用场景「撞墙」预测

输入你的使用场景，AI 会基于产品参数给出警告：

> "基于物理参数，这款 2000 流明投影仪在你的全天采光客厅里，对比度会下降 80%，建议放弃。"

### 📁 Agent C: 全网黑历史追溯

深挖产品/品牌的历史问题：
- 官方召回事件
- 集体投诉缺陷
- 换壳重生（某缺陷产品的改款）
- 品牌黑历史

## 🎨 UI 设计

- **实验室报告风格**：不像购物网站，像「避坑黑榜」
- **避坑指数进度条**：从「可以一试」到「快跑！」
- **吐槽热力图**：直观显示用户最不满意的模块
- **替代方案建议**：劝退后给你指条明路

## 🚀 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 API Key（可选）

复制 `env.example.txt` 为 `.env`，填入你的 API Key：

```
OPENAI_API_KEY=your_openai_api_key_here
```

> **注意**：不配置 API Key 也能运行，会使用内置的演示数据。

### 3. 启动服务

```bash
python run.py
```

访问 http://localhost:8000 开始使用！

## 📁 项目结构

```
电商选品器/
├── backend/
│   ├── agents/
│   │   ├── base_agent.py      # Agent 基类
│   │   ├── denoise_agent.py   # 差评脱水机
│   │   ├── scenario_agent.py  # 场景撞墙预测
│   │   └── history_agent.py   # 黑历史追溯
│   ├── config.py              # 配置管理
│   ├── models.py              # 数据模型
│   └── main.py                # FastAPI 主应用
├── frontend/
│   ├── index.html             # 主页面
│   ├── styles.css             # 样式（实验室风格）
│   └── app.js                 # 前端逻辑
├── requirements.txt           # Python 依赖
├── run.py                     # 启动脚本
└── README.md                  # 项目说明
```

## 💡 差异化优势

| 特性 | 淘宝问问/京东京言 | Perplexity | The Last 5% |
|-----|-----------------|------------|-------------|
| 立场 | 卖货导向 | 中立聚合 | **劝退导向** |
| 差评分析 | ❌ 不敢做 | ⚠️ 浅层 | ✅ 深度脱水 |
| 场景预测 | ❌ 无 | ❌ 无 | ✅ 撞墙警告 |
| 黑历史 | ❌ 不可能 | ⚠️ 有限 | ✅ 深度追溯 |
| 广告 | 💰 满屏 | 🔸 少量 | ✅ **零广告** |

## 🎯 推荐使用场景

1. **高客单价产品决策**：扫地机器人、投影仪、人体工学椅
2. **避免冲动消费**：在下单前让 AI 泼一盆冷水
3. **对比竞品**：了解各产品的「硬伤」在哪里

## 🛣️ 后续规划

- [ ] 接入 Firecrawl 实时抓取评论数据
- [ ] 支持粘贴商品链接直接分析
- [ ] 增加更多垂直类目（护肤品、宠物用品等）
- [ ] 浏览器插件版本
- [ ] 付费深度报告功能

## 📄 License

MIT License

---

**The Last 5%** - 因为最后 5% 的细节，决定了你会不会后悔。
