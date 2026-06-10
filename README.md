# GitHub Star Ranking

实时抓取并展示 GitHub Trending 热门仓库的 Web 应用。

## 功能

- 抓取 GitHub Trending 页面数据（日榜 / 周榜 / 月榜）
- 按编程语言筛选
- 服务端缓存（2 小时 TTL），后台定时刷新
- RESTful API 接口
- 响应式前端界面

## 技术栈

- **后端**: Flask + requests + BeautifulSoup
- **前端**: 原生 HTML / CSS / JavaScript
- **解析**: lxml

## 快速开始

```bash
cd github_star_rank
pip install -r requirements.txt
python app.py
```

访问 http://localhost:5000

## API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/trending?since=daily&language=python` | GET | 获取趋势仓库列表 |
| `/api/languages` | GET | 获取支持的语言列表 |
| `/api/refresh?since=daily` | POST | 强制刷新缓存 |

### 参数说明

- `since`: `daily` / `weekly` / `monthly`（默认 `daily`）
- `language`: 按语言筛选（如 `python`、`rust`）
- `force`: 设为 `1` 强制刷新缓存

## License

MIT