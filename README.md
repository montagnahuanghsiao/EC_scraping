# EC_scraping

使用 Python + Selenium 製作的 momo 購物網商品爬蟲。
可依關鍵字搜尋商品、支援多頁爬取，並擷取商品資訊與圖片，輸出為 JSON 與 CSV。

---

## 📌 功能

* 自動開啟 Chrome 並進入 momo
* 搜尋商品關鍵字
* 排除廣告商品
* LITE版本快速取得基本資訊
* ✅ 支援多頁爬取（可自訂頁數，限制 1~5 頁）
* ✅ 支援進入商品頁爬取更多細節
* 抓取：

  * 商品名稱
  * 商品價格
  * 商店名稱
  * 商品連結
  * 圖片連結
* 下載商品圖片
* 匯出 JSON / CSV

---

## 📁 專案結構

```
EC_scraping/
│
├─ momo_scraping.py
├─ requirements.txt
├─ README.md
│
├─ scraping_data/
│   ├─ momo_xxx.json
│   └─ momo_xxx.csv
│
└─ scraping_picture_關鍵字_時間/
    ├─ picture_1.webp
    └─ ...
```

---

## ⚙️ 環境需求

* Python 3.9+
* Google Chrome
* 穩定網路

---

## 🚀 安裝與執行

### 1️⃣ 下載專案

```
git clone https://github.com/montagnahuanghsiao/EC_scraping.git
cd EC_scraping
```

---

### 2️⃣ 建立虛擬環境

```
python -m venv venv
```

---

### 3️⃣ 啟動虛擬環境

#### Windows (PowerShell)

```
.\venv\Scripts\Activate
```

#### macOS / Linux

```
source venv/bin/activate
```

---

### 4️⃣ 安裝套件

```
pip install -r requirements.txt
```

或：

```
python -m pip install -r requirements.txt
```

---

### 5️⃣ 執行程式

```
python momo_scraping.py
```

---

### 6️⃣ 輸入關鍵字與頁數

```
請輸入關鍵字: 手機
請輸入要爬幾頁（1~5）: 2
```

---

## 🔄 爬蟲流程

1. 進入 momo 首頁
2. 輸入關鍵字搜尋商品
3. 抓取當前頁商品清單（排除廣告）
4. 逐一進入商品頁抓取詳細資料
5. 翻到下一頁（直到達到指定頁數）
6. 重複步驟 3~5
7. 最後統一儲存資料

---

## 📊 輸出結果

### 📁 商品資料

```
scraping_data/
  momo_關鍵字_時間.json
  momo_關鍵字_時間.csv
```

### 🖼 商品圖片

```
scraping_picture_關鍵字_時間/
  picture_1.webp
  picture_2.webp
```

---

## 📄 資料欄位

| 欄位           | 說明   |
| ------------ | ---- |
| number       | 商品編號 |
| product_name | 商品名稱 |
| sales_price  | 商品價格 |
| store        | 商店名稱 |
| product_url  | 商品連結 |
| picture_url  | 圖片連結 |

---

## ⚠️ 注意事項

* momo 網站可能改版，需更新 selector
* 過於頻繁請求可能被封鎖
* 本專案僅供學習用途
* 建議設定較小頁數（1~3 頁）進行測試

---

## ❗ 常見問題

### PowerShell 無法啟動虛擬環境

```
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

---

### pip 安裝失敗

```
python -m pip install -r requirements.txt
```

---

### cd 錯誤

```
pwd
ls
```

---

### 翻頁失敗（常見）

可能原因：

* 網頁尚未載入完成
* 下一頁按鈕 selector 改變
* 網站動態載入未更新

建議確認：

```
a.page-btn.page-next
```

---

## 🔧 改善方向

* 使用 logging 取代 print（提升除錯能力）
* 改寫成 class 架構（提升可維護性）
* 加入 headless 模式（背景執行）
* 圖片格式自動判斷（避免副檔名錯誤）
* CLI 參數（如 --keyword、--pages）

---

## 📦 requirements.txt

```
requests
selenium
webdriver-manager
pandas
```

---

## 👤 作者

```
Mountain Huang
```
