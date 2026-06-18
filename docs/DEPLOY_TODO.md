# 部署 TODO

## 前置条件
- [x] 代码已推送到 GitHub
- [x] PR 已合并到 main
- [x] Procfile 已添加（Railway 启动配置）
- [x] CORS 已更新（允许 Vercel 域名）

## 第 1 步：部署后端到 Railway
1. 打开 https://railway.com，用 GitHub 账号登录
2. 点 **New Project** → **Deploy from GitHub repo**
3. 选择 `market-watch-dashboard` 仓库
4. Railway 会自动检测 `backend/Procfile` 并部署
5. 部署完后点 **Settings** → 复制域名（类似 `xxx.up.railway.app`）

## 第 2 步：部署前端到 Vercel
1. 打开 https://vercel.com，用 GitHub 账号登录
2. 点 **Add New Project** → 导入 `market-watch-dashboard` 仓库
3. **关键**：在环境变量里加一个：
   - `NEXT_PUBLIC_API_BASE` = `https://你的Railway域名`
4. 点 Deploy

## 部署后验证
- [ ] 前端域名能访问
- [ ] 后端 API 能响应
- [ ] 前端能正确加载后端数据
- [ ] 定时任务正常运行

## 免费额度参考
- Vercel：100 GB/月带宽，无限部署
- Railway：$5/月免费用量
