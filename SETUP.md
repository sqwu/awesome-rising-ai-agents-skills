# ⚙️ 自动化设置指南

本仓库支持每日自动扫描 GitHub Trending 和 X 平台热度数据，自动生成热门榜单。

## 🚀 快速开始

### 1. 注册 Apify 账号

1. 访问 https://apify.com
2. 使用 GitHub 账号登录（推荐）
3. 进入 **Settings → Integrations** 页面
4. 复制 **Personal API Token**

### 2. 配置 GitHub Secrets

1. 打开仓库页面 → **Settings → Secrets and variables → Actions**
2. 点击 **New repository secret**
3. 添加以下 Secrets：

| Secret 名称 | 值 | 说明 |
|:---|:---|:---|
| `APIFY_TOKEN` | 你的 Apify API Token | 必需，用于抓取数据 |
| `GITHUB_TOKEN` | 自动提供 | 由 GitHub 自动生成，用于推送更新 |

### 3. 验证设置

1. 进入仓库 **Actions** 页面
2. 选择 **Daily Agent Heat Scan** 工作流
3. 点击 **Run workflow** 手动触发一次
4. 等待运行完成（约 1-2 分钟）
5. 检查是否成功更新 README.md

---

## 📊 数据源说明

### GitHub Trending
- **Actor**: `viralanalyzer/github-trending-scraper`
- **数据**: 每日热门仓库、今日新增星标、语言分布
- **筛选**: 自动筛选与 AI Agent 相关的项目

### X (Twitter)
- **Actor**: `api-ninja/x-twitter-advanced-search`
- **关键词**: AI agent, agent skill, crewai, langgraph, autogen 等
- **筛选**: min_faves:10（至少 10 个赞）

---

## 🔧 自定义配置

### 修改扫描频率

编辑 `.github/workflows/agent-scan.yml`：

```yaml
on:
  schedule:
    - cron: '0 8 * * *'  # 每天 UTC 8点
```

Cron 格式参考：
- `'0 */6 * * *'` - 每 6 小时
- `'0 0,12 * * *'` - 每天 0点和12点
- `'0 8 * * 1'` - 每周一 8点

### 调整评分权重

编辑 `scan_agents.py` 中的 `calculate_score` 函数：

```python
# 综合评分算法
growth_score = min(stars_today * 5, 100)    # GitHub 星标增长 (50%)
mention_score = min(mentions * 10, 50)      # X 提及数 (30%)
potential_score = min(stars_total / 1000, 30)  # 总星标潜力 (20%)
```

### 添加更多数据源

在 `main()` 函数中添加新的扫描源：

```python
# 示例：添加 Reddit 扫描
reddit_data = scan_reddit(client)
```

---

## 💰 成本预估

| 数据源 | 单次请求 | 每日成本 |
|:---|:---:|:---:|
| GitHub Trending (50 repos) | ~$0.02 | ~$0.02 |
| X 搜索 (200 tweets) | ~$0.03 | ~$0.03 |
| **总计** | - | **~$0.05/天 ($1.5/月)** |

Apify 免费额度：每月 $5，足够使用 3 个月以上。

---

## 🐛 故障排查

### 工作流运行失败

1. 检查 **Actions → Daily Agent Heat Scan → 最新运行日志**
2. 确认 `APIFY_TOKEN` 是否正确设置
3. 确认 Apify 账号有余额

### 数据未更新

1. 检查 `data/agents.json` 是否生成
2. 检查工作流日志中的错误信息
3. 确认筛选逻辑是否过滤了所有结果

### Apify 限流

- 免费账号有每日请求限制
- 如遇限流，可调整扫描频率或升级付费计划

---

## 📚 相关链接

- [Apify 官方文档](https://docs.apify.com/)
- [GitHub Actions 文档](https://docs.github.com/actions)
- [Awesome Rising AI Agents 主仓库](https://github.com/sqwu/awesome-rising-ai-agents-skills)

---

如有问题，欢迎提交 [Issue](../../issues)！
