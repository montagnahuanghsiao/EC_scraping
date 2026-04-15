# EC_scraping

使用 Python + Selenium 製作的購物網商品爬蟲。
可依關鍵字搜尋商品、擷取商品資訊、下載圖片，並輸出為 JSON 與 CSV。

---

## 📌 功能

* 自動開啟 Chrome 並進入頁面
* 搜尋商品關鍵字
* 排除廣告商品
* 支援多頁爬取
* 抓取：

  * 商品名稱
  * 商品價格
  * 商店名稱
  * 商品連結
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
└─ scraping_picture_xxx/
    ├─ picture_1.webp
    └─ ...
```

---

## ⚙️ 環境需求

* Python 3.9+
* Google Chrome

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

或

```
python -m pip install -r requirements.txt
```

---

### 5️⃣ 執行程式

```
python momo_scraping.py
```

---

### 6️⃣ 輸入關鍵字

```
請輸入關鍵字: 手機
請輸入要爬幾頁: 預設限制範圍 1-5 頁
```

---

## 📊 輸出結果

### 📁 資料

```
scraping_data/
  momo_關鍵字_時間.json
  momo_關鍵字_時間.csv
```

### 🖼 圖片

```
scraping_picture_關鍵字_時間/
  picture_1.webp
  picture_2.webp
```

---

## 📄 資料欄位

| 欄位           | 說明   |
| ------------ | ---- |
| number       | 編號   |
| product_name | 商品名稱 |
| sales_price  | 價格   |
| store        | 商店   |
| product_url  | 商品連結 |
| picture_url  | 圖片連結 |

---

## ⚠️ 注意事項

* 網站改版可能導致爬蟲失效
* 請勿過度頻繁請求（避免被封）
* 僅供學習用途

---

## ❗ 常見問題

### PowerShell 無法啟動 venv

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

確認目前路徑：

```
pwd
ls
```

---

## 🔧 改善方向

* 使用 logging 取代 print
* 改寫成 class 架構
* 加入 headless 模式
* 圖片格式自動判斷
* CLI 參數（例如 keyword）

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
