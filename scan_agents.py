#!/usr/bin/env python3
"""
每日 AI Agent 热度扫描脚本
使用 Apify 抓取 GitHub Trending 和 X(Twitter) 数据
自动计算综合热度分数并更新 README
"""

import os
import json
import re
from datetime import datetime
from apify_client import ApifyClient

# 配置
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
DATA_DIR = "data"
AGENTS_JSON = f"{DATA_DIR}/agents.json"
AGENTS_CSV = f"{DATA_DIR}/agents.csv"

# 关键词配置（用于 X 平台搜索）
AGENT_KEYWORDS = [
    "AI agent", "agent skill", "open source agent",
    "autonomous agent", "multi-agent", "crewai",
    "langgraph", "autogen", "agent framework"
]

# 已知的热门 Agent 仓库（用于匹配和补充）
KNOWN_AGENTS = [
    {"name": "n8n", "owner": "n8n-io"},
    {"name": "langflow", "owner": "langflow-ai"},
    {"name": "AutoGPT", "owner": "Significant-Gravitas"},
    {"name": "crewAI", "owner": "crewAIInc"},
    {"name": "autogen", "owner": "microsoft"},
    {"name": "langgraph", "owner": "langchain-ai"},
    {"name": "ollama", "owner": "ollama"},
    {"name": "Qwen-Agent", "owner": "QwenLM"},
    {"name": "awesome-llm-apps", "owner": "Shubhamsaboo"},
    {"name": "camel", "owner": "camel-ai"},  # OWL
    {"name": "AgentForge", "owner": "DataBassGit"},
]


def scan_github_trending(client: ApifyClient) -> list:
    """扫描 GitHub Trending 获取热门 Agent 项目"""
    print("🔍 正在扫描 GitHub Trending...")
    
    try:
        run = client.actor("viralanalyzer/github-trending-scraper").call(run_input={
            "since": "daily",
            "languages": ["python", "typescript", "javascript", "rust", "go"]
        })
        
        dataset = client.dataset(run["defaultDatasetId"])
        items = dataset.list_items().items
        
        print(f"✅ GitHub Trending: 获取 {len(items)} 个仓库")
        return items
    except Exception as e:
        print(f"❌ GitHub Trending 扫描失败: {e}")
        return []


def scan_x_mentions(client: ApifyClient) -> list:
    """扫描 X 平台获取 Agent 相关讨论"""
    print("🔍 正在扫描 X 平台...")
    
    # 构建搜索查询
    query = " OR ".join([f'"{kw}"' for kw in AGENT_KEYWORDS[:5]])
    query += " min_faves:10"
    
    try:
        run = client.actor("api-ninja/x-twitter-advanced-search").call(run_input={
            "query": query,
            "search_type": "Latest",
            "numberOfTweets": 200,
            "since": datetime.now().strftime("%Y-%m-%d")
        })
        
        dataset = client.dataset(run["defaultDatasetId"])
        items = dataset.list_items().items
        
        print(f"✅ X 平台: 获取 {len(items)} 条推文")
        return items
    except Exception as e:
        print(f"❌ X 平台扫描失败: {e}")
        return []


def calculate_score(repo: dict, tweets: list) -> dict:
    """计算综合热度分数"""
    repo_name = repo.get("fullName", "")
    repo_short = repo.get("repo", "")
    
    # 基础分数
    stars_today = repo.get("starsToday", 0)
    stars_total = repo.get("stars", 0)
    forks = repo.get("forks", 0)
    
    # 计算 X 平台提及数
    mentions = 0
    for tweet in tweets:
        text = tweet.get("text", "").lower()
        if repo_short.lower() in text or repo_name.lower() in text:
            mentions += 1
    
    # 综合评分算法
    # - starsToday 权重最高 (0.5)
    # - X 提及数 (0.3)
    # - 总星标增长潜力 (0.2)
    growth_score = min(stars_today * 5, 100)  # 封顶100
    mention_score = min(mentions * 10, 50)     # 封顶50
    potential_score = min(stars_total / 1000, 30)  # 封顶30
    
    total_score = growth_score * 0.5 + mention_score * 0.3 + potential_score * 0.2
    
    return {
        "name": repo_name,
        "url": repo.get("repoUrl", ""),
        "description": repo.get("description", ""),
        "language": repo.get("language", ""),
        "stars_total": stars_total,
        "stars_today": stars_today,
        "forks": forks,
        "x_mentions": mentions,
        "score": round(total_score, 2),
        "updated": datetime.now().isoformat()
    }


def filter_agent_repos(repos: list) -> list:
    """筛选与 Agent 相关的仓库"""
    agent_keywords = [
        "agent", "ai", "llm", "automation", "workflow",
        "crewai", "langgraph", "autogen", "bot"
    ]
    
    filtered = []
    for repo in repos:
        text = f"{repo.get('description', '')} {repo.get('repo', '')}".lower()
        if any(kw in text for kw in agent_keywords):
            filtered.append(repo)
    
    return filtered


def generate_readme_table(agents: list) -> str:
    """生成 README 中的表格内容"""
    # 取前15名
    top_agents = sorted(agents, key=lambda x: x["score"], reverse=True)[:15]
    
    lines = [
        "## 📊 今日热门榜单（自动更新）",
        "",
        "| 排名 | 项目 | 今日新增⭐ | X提及 | 综合热度 |",
        "|:---:|:---|:---:|:---:|:---:|",
    ]
    
    for i, agent in enumerate(top_agents, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}"
        name_link = f"[{agent['name']}]({agent['url']})"
        stars = agent['stars_today']
        mentions = agent['x_mentions']
        score = f"{agent['score']:.1f}"
        
        lines.append(f"| {emoji} | {name_link} | +{stars} | {mentions} | {score} |")
    
    lines.extend([
        "",
        f"*最后更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        "---",
        "",
    ])
    
    return "\n".join(lines)


def update_readme(table_content: str):
    """更新 README.md 文件"""
    readme_path = "README.md"
    
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 查找标记位置
    start_marker = "## 📊 今日热门榜单"
    end_marker = "## 🤖 自主代理"
    
    if start_marker in content and end_marker in content:
        # 替换旧内容
        pattern = f"{re.escape(start_marker)}.*?{re.escape(end_marker)}"
        new_section = table_content + end_marker
        content = re.sub(pattern, new_section, content, flags=re.DOTALL)
        
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ README.md 已更新")
    else:
        print("⚠️ 未找到替换标记，跳过 README 更新")


def save_data(agents: list):
    """保存数据到文件"""
    # 确保目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # 保存 JSON
    with open(AGENTS_JSON, "w", encoding="utf-8") as f:
        json.dump(agents, f, indent=2, ensure_ascii=False)
    
    # 保存 CSV（便于数据分析）
    if agents:
        import csv
        with open(AGENTS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=agents[0].keys())
            writer.writeheader()
            writer.writerows(agents)
    
    print(f"✅ 数据已保存: {AGENTS_JSON}, {AGENTS_CSV}")


def main():
    print(f"🚀 开始每日 Agent 热度扫描 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)
    
    if not APIFY_TOKEN:
        print("❌ 错误: 未设置 APIFY_TOKEN 环境变量")
        return
    
    # 初始化客户端
    client = ApifyClient(APIFY_TOKEN)
    
    # 1. 扫描 GitHub Trending
    github_repos = scan_github_trending(client)
    
    # 2. 筛选 Agent 相关仓库
    agent_repos = filter_agent_repos(github_repos)
    print(f"🎯 筛选出 {len(agent_repos)} 个 Agent 相关仓库")
    
    # 3. 扫描 X 平台
    tweets = scan_x_mentions(client)
    
    # 4. 计算分数
    agents = []
    for repo in agent_repos:
        agent_data = calculate_score(repo, tweets)
        if agent_data["score"] > 0:  # 只保留有热度的
            agents.append(agent_data)
    
    # 按分数排序
    agents.sort(key=lambda x: x["score"], reverse=True)
    
    print(f"\n📈 扫描完成！发现 {len(agents)} 个上升中 Agents")
    
    # 5. 保存数据
    save_data(agents)
    
    # 6. 生成并更新 README
    if agents:
        table = generate_readme_table(agents)
        update_readme(table)
        
        # 打印 TOP 5
        print("\n🏆 TOP 5 热门项目:")
        for i, agent in enumerate(agents[:5], 1):
            print(f"  {i}. {agent['name']} - 热度: {agent['score']:.1f} (+{agent['stars_today']}⭐, {agent['x_mentions']}提及)")
    
    print("\n✨ 全部完成！")


if __name__ == "__main__":
    main()
