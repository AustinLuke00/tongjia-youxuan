# 童价优选：网页采集与人工核验版

## 运行网站
`python3 -m http.server 8080` 后访问 `http://localhost:8080`。

## 采集公开商品页面（人工触发）
1. 在 `data/urls.txt` 每行放一个允许访问的公开 HTTPS 商品详情页 URL。
2. 运行 `python3 scripts/collect.py`，或 GitHub Actions 中手动运行 `Collect public product metadata`，下载 `pending-product-review` artifact。
3. 查看 `data/candidates.json`。仅解析网页中 JSON-LD Product 结构化数据；没有则为空，不尝试绕过登录、验证码、风控或反爬机制。严格遵守 robots.txt，最多处理20条链接，逐条间隔2秒。
4. 人工核验商品链接、店铺经营主体、品牌授权/平台自营证据、SKU/规格和价格时间后，才可以在 `data/approved.json` 填写审核记录。采集结果**绝不自动成为已核验商品**。
5. 运行 `python3 scripts/publish.py`，生成 `data/products.json`，提交到 GitHub。网站自动加载审核商品；若没有审核商品，继续明确展示演示数据。

## approved.json 单条格式（仅示例字段，不代表真实商品）
```json
[{"status":"approved","merchant_verified":true,"evidence_url":"https://example.com/evidence","reviewed_at":"2026-10-13T00:00:00Z","priced_at":"2026-10-13T00:00:00Z","title":"商品标题","brand":"品牌","sku":"SKU-001","spec":"同款规格","merchant":"已核验商家名称","platform":"京东","category":"纸尿裤","url":"https://example.com/product","price":99.9}]
```
**注意**：审核时间超过30天或价格超过24小时的数据不发布；审核字段由人工据真实证据填写，不得虚构。正式运营还应维护商家授权证据有效期、异常报警、定时清理和平台数据使用许可。GitHub Pages 无法运行采集脚本，只能显示发布后的 JSON。各平台公开网页可能拒绝抓取，不能保证实时价格和抓取成功率。
