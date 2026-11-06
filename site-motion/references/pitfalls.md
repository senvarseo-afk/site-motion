# 風險與陷阱

證據等級：**官方**、**社群**（共識但無官方專文）、**實務**（實際專案踩過，不代表普遍成立）。查證日 2026-11-06，超過 90 天的項目用前先重新確認。

## 變現與分析（靠廣告的站最先看）

**先決定導覽做法**：同文件軟導覽要自己處理分析和廣告，跨文件轉場是真實換頁，兩者都不用改。廣告的不確定性無法接受時，選跨文件。

**GA4 軟導覽 page_view**（官方，developers.google.com/analytics/devguides/collection/ga4/single-page-applications）
Enhanced measurement 的「Page changes based on browser history events」開著時，GA4 會自動送 page_view，此時再手動送就會重複計算。二選一：

- 用 history 事件：不寫程式，但 `gtag('config', ...)` 帶的自訂參數不會隨頁更新。
- 手動送：到 GA4 後台關掉 history 事件（`send_page_view: false` 只管 config 那一次，關不掉它），在切頁完成事件送 `page_view`，帶 `page_location`、`page_title` 與自訂參數，首次載入避免重複。

這個 history 事件預設是開的，部署文件要寫清楚開或關。

驗收用 DebugView 確認每次切頁只有一個 page_view，`page_location` 與 `page_referrer` 正確。沒有真實 ID 時，用假 ID 建置並讀 `dataLayer`，驗完用無 ID 重建，不要把假 ID 留在產出。

**廣告與軟導覽**（官方規則部分，SPA 處理為社群）
AdSense 官方政策不允許未經使用者要求就重新整理頁面或頁面元素，但沒有 SPA 專文，用前再查最新說明。保守做法：

- 使用者導覽到新內容時，舊單元隨內容移除，在新內容插入新的 `<ins>`，對每個新單元只 push 一次
- 不對既有單元計時或依可見度重新整理
- 自動廣告在客戶端導覽後不一定重新掃描，軟導覽站以手動單元為主；錨定與插頁廣告也要實測
- 廣告放在會被換掉的內容區，不放進持久外框
- 廣告不放進有動畫的父層，也不放進抽屜、分頁、收合區，初始隱藏的單元可能不發請求

**上線前必須決定**：同文件軟導覽加廣告要實測後才開。跨文件做法的代價是不支援的瀏覽器沒有轉場、外框不算真的持久、倒數等狀態要在新頁重建，但功能和收入都不受影響。跨文件轉場與插頁廣告的互動也要實測。

**原地切換的收入代價**（實務判斷）：原地操作不產生新頁面，就沒有新的廣告請求。靠多看一頁賺錢的站，換內容要真換頁。

**廣告版面**（官方與社群）
廣告容器預留 `min-height`。動效不能把內容推到使用者手指下方造成誤觸，通知和抽屜不蓋住廣告。錨定廣告在底部時，底部導覽等於貼著廣告，要在提案裡標出來，原型要放廣告佔位。

## SEO

- 每個頁面維持獨立可索引網址，原地切換只是增強
- 初始 HTML 內容不能變少，tab 和手風琴的內容要在 HTML 裡
- 橫滑和日期切換要有真實 `<a href>`，爬蟲才走得到
- 改版前後比對 title、H1、canonical、robots、結構化資料

## Core Web Vitals

門檻 LCP ≤ 2.5s、INP ≤ 200ms、CLS ≤ 0.1，以第 75 百分位為準（官方，web.dev/articles/vitals）。

- 只動 `transform` 與 `opacity` 不觸發 CLS
- 使用者輸入後 500ms 內的位移不計入 CLS（官方，web.dev/articles/cls）。資料更新、通知等非使用者觸發的動效不能推動版面
- Hero 進場動畫會拖慢 LCP，首屏主要內容不要等動畫，LCP 元素不做淡入
- 跨文件的根層淡入是例外：從搜尋進站的第一頁沒有舊頁可轉，不會觸發轉場。站內換頁仍要實測 LCP，變差就把淡入改短或移除
- 現有 LCP 或 INP 已不達標時，先修效能，動效只做按壓回饋
- 軟導覽：Chrome 2026-10 起在 CrUX 提供 experimental 軟導覽指標，穩定版分數不變（官方，web.dev/blog/crux-experimental-soft-navs）。穩定分數看不到軟導覽後的問題，不代表沒有問題
- 跨文件轉場：導覽超過 4 秒會被跳過（官方，developer.chrome.com/docs/web-platform/view-transitions/cross-document）
- 字體閃動會讓轉場看起來抖，preload 關鍵字體並調 fallback 度量

## 瀏覽器支援（2026-11 查證，用前重查）

| 功能 | 支援 |
|---|---|
| 同文件 View Transitions | Chrome／Edge 111+、Safari 18+、Firefox 144+ |
| 跨文件 View Transitions | Chrome／Edge 126+、Safari 18.2+；Firefox 查到的資料為尚未支援 |

不支援時要退回一般換頁，功能不能壞。

社群 App 的內建瀏覽器支援情況查不到可靠資料，也可能和系統返回手勢衝突，流量多來自社群時驗收要實測。測試機要含一支中階 Android。

## Astro ClientRouter（實務，規則見 docs.astro.build）

其他框架有對應的切頁事件，思路相同。

- 打包的 module script 只跑一次，DOM 綁定寫在 `astro:page-load`
- 每頁要重跑的 inline script 加 `data-astro-rerun`，並加重複綁定保護
- `DOMContentLoaded` 切頁後不會再觸發
- 首次 `astro:page-load` 綁在 window load，首筆 page_view 建議在 DOMContentLoaded 送，否則慢網路會漏掉提早離開的訪客
- Astro 用腳本的 src 或文字判斷是否跑過。分析設定若每頁文字不同，遇到新內容會重跑。讓 inline script 全站逐字相同，每頁參數放 `<body data-*>`，送出當下才讀
- 同路徑不重送 page_view，避免背景刷新多算一筆
- ClientRouter 不會更新 `document.referrer`，需要頁面層級來源報表時手動送 `page_referrer`
- 持久元素的選中狀態不會自己更新，要在切頁後重算
- `location.reload()` 會破壞連續感，改 `navigate(location.href)`
- 全域定時器在切頁後還在跑，查詢 DOM 前要確認節點存在
- 頁面專屬腳本（計算機、表單工具）改版後要逐一重測
- **`transition:name={undefined}` 仍算掛了指令**：共用元件寫 `transition:name={name}` 時，沒傳值的實例會被自動命名，產生大量 CSS，名稱依頁面順序編號，不同頁可能誤配。曾有列表頁 158KB 裡 100KB 是轉場 CSS。改成只在有值時才輸出指令
- 上線後要看建置結果的 HTML 大小，不只看原始碼

## 互動實作（實務）

- `pointerleave` 收尾時不要重繪面板，否則剛展開的列會被收回
- `overflow: hidden` 的容器仍可能被 focus 或 `scrollIntoView` 捲動，造成內容橫移。在該容器監聽 `scroll` 把 `scrollLeft` 歸零
- 展開列在滑動容器內時，點擊和拖曳要用位移量區分
- 窄欄裡的數字或標籤會換行，展開區要縮小元素並 `flex-wrap: nowrap`
- 暗色模式下寫死色值的元素會看不見
- 可及性：`aria-expanded`、鍵盤可操作、`prefers-reduced-motion` 全關
