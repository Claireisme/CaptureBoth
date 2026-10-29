# CaptureBoth 产品网站

默认英文，另有法语、意大利语、德语、西班牙语、日语、韩语、葡萄牙语、繁体中文，共 9 种网站语言。每种语言均有产品介绍、使用帮助和隐私政策，共 27 个页面。品牌署名 Eastwood；完整发布主体为 Eastwood Management Services Limited，公开支持邮箱为 CaptureBoth@520.ie。

无框架、无依赖包、无数据库和后端。`dist/` 为已生成的完整静态网站，可以直接部署到 Cloudflare Pages。

## 直接上传到 Cloudflare Pages

1. 登录 Cloudflare Dashboard，进入 **Workers & Pages**。
2. 点击 **Create application**，进入 **Pages** 的上传静态文件入口（Direct Upload / Drag and drop）。
3. 创建项目，例如 `captureboth`；实际项目名按账号内可用情况选择。
4. 上传本目录生成的 `release/CaptureBoth-Cloudflare-Pages.zip`，或直接拖入 `dist/`。
5. 点击 **Deploy site / Save and Deploy**，使用 Cloudflare 返回的真实 `pages.dev` 地址访问网站。
6. 检查首页、语言切换、支持页面、隐私页面以及邮箱链接。

ZIP 根目录直接包含 `index.html`、`assets/`、`fr/`、`it/`、`de/` 等语言目录及 `_headers`，不需要再套一层文件夹。上传的是网站 ZIP，不是 App Store 截图资料 ZIP。不要为提交审核的支持和隐私页面开启登录访问限制。

[Cloudflare Direct Upload 官方说明](https://developers.cloudflare.com/pages/get-started/direct-upload/)

## 网页地址

将部署后的实际站点域名加上以下路径：

| 语言 | 产品介绍 | 使用帮助 | 隐私政策 |
| --- | --- | --- | --- |
| English（默认） | `/` | `/support.html` | `/privacy.html` |
| Français | `/fr/` | `/fr/support.html` | `/fr/privacy.html` |
| Italiano | `/it/` | `/it/support.html` | `/it/privacy.html` |
| Deutsch | `/de/` | `/de/support.html` | `/de/privacy.html` |
| Español | `/es/` | `/es/support.html` | `/es/privacy.html` |
| 日本語 | `/ja/` | `/ja/support.html` | `/ja/privacy.html` |
| 한국어 | `/ko/` | `/ko/support.html` | `/ko/privacy.html` |
| Português | `/pt/` | `/pt/support.html` | `/pt/privacy.html` |
| 繁體中文 | `/zh-hant/` | `/zh-hant/support.html` | `/zh-hant/privacy.html` |

语言菜单使用各语言原生名称，切换时保留当前页面和章节。不会按浏览器语言自动改变默认英文。旧版 `/en/` 和 `/en/support.html`、`/en/privacy.html` 通过永久重定向兼容。首页 `/` 为英文；简体中文网站已移除，旧的简体中文路径重定向至繁体中文页面。

Cloudflare Pages 可能将 `.html` 地址规范化为无扩展名地址，使用浏览器最终显示的完整 HTTPS 地址填写 App Store 即可。旧的 `/privacy-en.html`、`/privacy-zh-Hans.html`、`/support-en.html`、`/support-zh-Hans.html` 已在 `_redirects` 中映射到相应页面。

## 取得域名和 App Store 链接后

编辑 `site.config.json`：

- `siteURL`：真实站点来源地址，例如实际的 `https://…pages.dev`，不含子目录。空值时不生成虚构的 canonical 或 sitemap 地址。
- `appStoreURL`：真实 App Store 产品链接。尚未配置时显示“即将登陆 App Store”；配置后底部入口变成真实下载链接。
- `brandPublisher`：简短品牌署名，当前为 Eastwood。

公开公司名、邮箱和英文 App 隐私政策正文来自主工程 `CaptureBoth/Resources/PrivacyPolicy.json`。独立网站仓库使用 `data/privacy-policy.json` 中的英文快照，不依赖 iOS 工程。后续 App 政策有更新时，应同步快照并复核译文。其余语言的译文保存在 `locales/`，记录了英文原文摘要值；原文变化时构建会要求复核译文。网站额外提供“网站访问与支持邮件”章节，说明 Cloudflare 托管和用户主动邮件反馈的数据处理。

取得站点实际地址后，也应将 App 隐私资源的 `privacyURL`、`supportURL` 回填为真实地址。修改后重新生成并上传网站；下次归档 App 会包含最新隐私联系资料。

## 本地修改与构建

进入本网站目录后执行（独立克隆的网站仓库也适用）：

```bash
python3 build.py
python3 verify.py
```

预览：

```bash
python3 -m http.server 4173 --bind 127.0.0.1 --directory dist
```

打开 `http://127.0.0.1:4173/`。源文件在 `build.py`（页面生成）、`locales/*.json`（各语言文案）、`src/style.css`、`src/site.js`、`assets/`；构建会更新 `dist/` 与上传 ZIP。在完整 App 工程内，ZIP 输出到上级 `release/`；独立网站仓库则输出到本目录 `release/`。生成器使用 Python 标准库，不需要安装依赖。`dist/` 是生成目录，重建时会完整替换；请编辑源文件。

如果使用 Git 自动部署，可将已构建网站提交到 Git，Cloudflare Pages 选择无框架，构建命令 `exit 0`，输出目录指向已提交的 `dist/`。只将 `dist/` 单独作为仓库时，输出目录用仓库根目录。源文件变更后，重新构建并提交 `dist/`。独立网站仓库的 Cloudflare Pages 根目录留空，输出目录填写 `dist`，构建命令可填写 `python3 build.py`。[静态 HTML 部署说明](https://developers.cloudflare.com/pages/framework-guides/deploy-anything/)

## 图片与功能范围

- 网站使用现有暖灰 App 图标，以及实际 App 界面截图。JPEG 是为网页显示按比例缩小和转码的完整 UI 截图，没有改写界面按钮或拍摄内容。
- 截图中的人物与场景是先前生成的示例素材，页面已标注，不声称是设备实拍画质。来源位于 `assets/store-screenshots/release67/`。
- 本网站无表单、登录、广告、分析 SDK、媒体上传或数据库。反馈按钮仅在浏览器本地复制文字，不自动发邮件。
- `_headers` 限制网页使用相机、麦克风与定位，并仅加载站内脚本、样式和图片。Cloudflare 托管可能处理请求与 IP 等技术信息，已在网页隐私说明中区分。
- 新增语言仅用于网站。App 本身仍支持英文与简体中文，帮助页已明确说明；不会为网站新语言虚构本地化的 App 界面截图。所有网站语言均使用英文 App 截图，繁体中文页已标注画面语言。
- 双摄设备要求按实际 App 能力填写：iOS 17.2+，需要支持同时前后采集的实体 iPhone；iPhone 11 已用于实机验证。不宣称所有 iPhone 均支持。

当前交付为本地网站与 Cloudflare 上传包，未替用户创建 Cloudflare 项目或执行公网部署。
