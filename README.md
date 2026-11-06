# site-motion

網站動畫與互動的評估 skill。它會先診斷問題，再規劃 2 到 3 個版本並做可點的手機原型，使用者選定後才實作。

採用 Agent Skills 開放格式（agentskills.io）。

## 安裝

下載這個 repo 後，把整個 `site-motion` 資料夾放進你的 agent 讀取 skill 的目錄，資料夾名稱不要改。各工具的目錄不同，請看該工具的文件。

```bash
git clone https://github.com/senvarseo-afk/site-motion.git
```

不支援 skill 的工具，可以把 `SKILL.md` 內容貼給它，並提供 `references/` 裡需要的檔案。

## 需求

- 稽核腳本需要 Python 3.9 以上，不用安裝套件
- 範本是單一 HTML，不用建置工具
- 瀏覽器工具與託管頁面是選用的，沒有時 skill 會要求標明未驗證

## 怎麼用

對 agent 說「幫我評估網站動畫」或「網站太死板」，或直接說要用 site-motion。內容以繁體中文撰寫，agent 會用使用者的語言回覆。
