# 動效配方

參數來自實際上線網站的做法，可依品牌調整。預設緩動 `cubic-bezier(.2, .8, .2, 1)`，主要只動 `transform` 與 `opacity`，高度展開例外用 grid。

## 時長基準

| 用途 | 時長 |
|---|---|
| 按下壓感 | 100 到 120ms |
| 指示條、tab 底線 | 250 到 280ms |
| 展開收合 | 280ms |
| 面板滑動 | 320ms |
| 頁面轉場 | 舊頁 140ms，新頁 240ms；跨文件做法只用淡入，不位移 |
| 共享元素 | 340ms |
| 通知滑入 | 350ms，停留 3 到 7 秒 |
| 更新高亮淡出 | 900 到 1200ms |

超過 400ms 的介面動效會讓人覺得慢，只有敘事時刻例外。

## A 級：回饋（不動架構）

**按下壓感**：列、按鈕、chip、底導都要有。

```css
.row:active, .btn:active { transform: scale(.97); transition: transform .1s; }
```

**資料更新高亮**：輪詢更新時，只對真的變動的節點加 class，否則使用者分不出有沒有更新。

```css
.changed { animation: changed .9s ease; }
@keyframes changed { from { background: color-mix(in srgb, var(--accent) 15%, transparent); } to { background: transparent; } }
```

**相對時間**：「Updated 12:08」改成每秒跳的「20s ago」，比任何動畫都更能證明網站是活的。

**倒數**：60 分鐘內每秒更新，歸零時原地切換狀態，不重載。

**滑動指示條**：tab 或底導的底線用 `left` 與 `width` 過渡，不要跳。這是脫離文件流的小元素，不會造成 CLS。

**數字滾動**：只用於氣氛數字，一個 session 跑一次（`sessionStorage`），伺服器 HTML 放最終值。比分、價格、結果這類權威資料不跑假數字，截圖或爬蟲可能抓到過程值。

**權威資料的進場**：同一筆資料只在第一次看到時播放，回上一頁與重訪直接顯示。使用者是來核對，不是來看表演。

## B 級：連續（改導覽模型）

**跨文件轉場**（有廣告的站預設用這個）：每頁仍是真實載入，刪掉這段就回到一般換頁，退路最乾淨。

```css
@view-transition { navigation: auto; }
header { view-transition-name: site-header; }
nav.bottomnav { view-transition-name: bottomnav; }
```

共享元素一樣用 `view-transition-name`，名稱在單頁內必須唯一。搭配 speculation rules 的 prefetch 讓下一頁夠快。有廣告的站先不用 prerender，廣告平台對 prerender 的處理要先查清楚。

**軟導覽與持久外框**（通過導覽閘門才用）。Astro 範例：

```astro
<ClientRouter />
<header transition:persist="header">...</header>
<nav class="bottomnav" transition:persist="bottomnav">...</nav>
```

頁首、底導持久化後，倒數與輪詢不重置。Next.js、Nuxt、SvelteKit 把外框放在共用 layout 就有同樣效果，頁面轉場的支援方式依版本不同，實作前查該框架當下的文件。Astro 的 ClientRouter 預設 prefetch 是 hover，手機上幾乎沒作用，列表要改 `tap` 或 `viewport`。

**頁面轉場**：

```css
::view-transition-old(root) { animation: 140ms ease both vt-out; }
::view-transition-new(root) { animation: 240ms cubic-bezier(.2, .8, .2, 1) both vt-in; }
@keyframes vt-out { to { opacity: 0; } }
@keyframes vt-in { from { opacity: 0; transform: translateY(6px); } }
```

**共享元素**：列表的圖片或主要資料飛到內頁頁首，使用者看得到自己從哪來。兩頁同一元素設相同的名稱，名稱含 id 確保全頁唯一。只命名真的要飛的元素。LCP 元素不要做共享元素。

**原地展開**：

```css
.det { display: grid; grid-template-rows: 0fr; transition: grid-template-rows .28s cubic-bezier(.2, .8, .2, 1); }
.open .det { grid-template-rows: 1fr; }
.det > div { overflow: hidden; }
```

展開內容要在初始 HTML 裡，不要點了才載入，否則搜尋引擎看不到。這是規則「只動 transform 與 opacity」的例外：使用者輸入後 500ms 內的位移不計入 CLS，所以時長要低於 300ms，而且只由使用者點擊觸發。下方緊鄰廣告時，廣告會被推動，改把展開區放在廣告下方。

`overflow: hidden` 會切掉泰文上標元音等字形，這類語言的展開容器要留足行高與 padding，並實際看過。

**底部抽屜**：短內容用抽屜原地開，不離開頁面。底部有錨定廣告時會互相遮蓋，這類站改用原地展開，或先實測。

**合併物件**：把重複卡片併成一塊板，列之間用 1px 分隔線。這是版面微調，但對「一堆物件」的感覺效果最大，提案時要明列讓使用者同意。

**原地篩選**：同頁資料用 `data-*` 顯示或隱藏，帶 200ms 淡入，原本的獨立網址保留給 SEO。

## C 級：App 感

**手勢橫滑**：pointer events 判斷方向，水平才接管，`touch-action: pan-y` 留給垂直捲動。邊界加 0.3 倍阻尼，超過 20% 寬度才切換。一定要有真實 `<a href>` 作為基礎，避開左右邊緣約 20px 留給系統返回，滑桿與時間軸這類元件要排除，例如 `data-no-swipe`。切換目標要在同類頁面內。

**骨架換資料**：換資料時閃約 260ms 骨架，再帶方向滑入。

**即時通知**：頂端滑入一條事件通知，點了捲到該處並展開高亮。不擋主要操作，也不蓋住廣告。只用在資料真的即時的站，假即時不要做。

**狀態原地切換**：內容狀態改變時先原地更新，再由背景刷新，取代 `location.reload()`。

## 敘事動畫（品牌頁）

一頁一個時刻，放在 Hero 或一個關鍵段落。優先 CSS 與 Scroll-driven animations，真的需要時間軸才用 GSAP，向量動畫才用 Lottie。靜態狀態要完整可讀，動畫只是加分。資料站與文章站不做捲動淡入。

函式庫授權與體積每次都查當下版本，不要憑記憶報數字。

## 模板感的判斷

有反饋感的動態由使用者動作或真實資料變化觸發。頁面載入或捲動到就自己播放的，看起來就是模板。三個問題：

1. 這個動畫是誰觸發的？答案是「頁面自己」就很可能是模板。
2. 拿掉它，使用者會少知道什麼？什麼都不會少就刪。
3. 把站名換掉，它放在別的站也成立嗎？成立就代表沒有個性，動態要來自這個站的主題。

## 不要做

- 每個區塊都捲動淡入、卡片排隊彈入、所有卡片 hover 浮起
- 捲動淡入用在資料區塊：內容慢半拍，還可能卡在 `opacity: 0`
- 對 LCP 元素（Hero 圖、H1）做淡入、模糊或延遲
- 泰文、阿拉伯文、印地文等用逐字動畫或文字遮罩滑入：會拆開組合字元或切掉字形
- 每次進頁都重跑的動畫
- 用 `top`、`height`、`margin` 做主要動畫
- `transition: all`
- 動畫中的按鈕不可點
- 為了動而動的循環動畫，狀態指示除外
