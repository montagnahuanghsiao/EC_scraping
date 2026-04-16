import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
)

import time
import json
import pandas as pd
from datetime import datetime
import os
import random

# 1. 設定瀏覽器的參數 (Options)
options = Options()
# options.add_argument("--headless")  # 如果不想看到瀏覽器視窗跳出來，把這行註解拿掉
options.add_argument("--start-maximized")  # 啟動時視窗最大化
options.add_argument("--incognito")  # 使用無痕模式
options.add_argument("--disable-popup-blocking")  # 停用 Chrome 的彈窗阻擋功能。
# 重要：隱藏自動化控制特徵，避免被網站阻擋
options.add_argument("--disable-blink-features=AutomationControlled")
# options.add_argument("user-agent=") --> 補一個常見的 User-Agent，提高存活率
options.add_experimental_option(
    "excludeSwitches", ["enable-automation"]
)  # 隱藏「受自動控制」提示
options.add_experimental_option("useAutomationExtension", False)


# 2. 自動下載並啟動 Chrome
# ChromeDriverManager 會處理版本匹配問題
def create_driver():
    service = ChromeService(executable_path=ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


# 3. 測試：前往 Google 並關閉
# driver.get("https://www.google.com")
# print(f"網頁標題是: {driver.title}")
# 完成後記得關閉，否則電腦會殘留一堆背景 Chrome 程序
# driver.quit()


def close_ad_overlay(driver, wait):
    try:
        # 先找遮罩
        overlay = driver.find_element(By.CSS_SELECTOR, "[data-testid='ad-overlay']")

        if overlay.is_displayed():
            print("偵測到廣告遮罩，嘗試關閉...")

            # 常見情況 1：有關閉按鈕
            close_buttons = driver.find_elements(
                By.CSS_SELECTOR,
                "[data-testid='ad-overlay'] button, \
                 [data-testid='ad-overlay'] [aria-label='close'], \
                 [data-testid='ad-overlay'] .close, \
                 [data-testid='ad-overlay'] .btn-close",
            )

            for btn in close_buttons:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        driver.execute_script("arguments[0].click();", btn)
                        time.sleep(1)
                        return
                except:
                    pass

            # 常見情況 2：沒有明顯關閉鈕，就等它消失
            wait.until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, "[data-testid='ad-overlay']")
                )
            )

    except Exception:
        # 沒找到遮罩就略過
        pass


def search_product(driver, keyword):
    # 設定最長等待 10 秒
    wait = WebDriverWait(driver, 10)

    try:
        # 1. 等待搜尋框出現 (確保網頁載入完成)
        product_search = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[name='search-input']")
            )
        )

        # 2. 清空並輸入關鍵字
        product_search.clear()
        product_search.send_keys(keyword)

        # 3. 等待搜尋按鈕可以被點擊，然後點下去
        search_btn = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button[data-testid='header-search-button']")
            )
        )
        # 先處理廣告遮罩
        close_ad_overlay(driver, wait)

        # 捲到按鈕位置
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", search_btn
        )
        time.sleep(0.5)

        # 記錄舊網址
        old_url = driver.current_url

        try:
            # 先用正常 click
            wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button[data-testid='header-search-button']")
                )
            )
            search_btn.click()

        except ElementClickInterceptedException:
            print("按鈕被遮住，改用 JS click")
            driver.execute_script("arguments[0].click();", search_btn)

        # 等待網址或結果區更新
        try:
            wait.until(lambda d: d.current_url != old_url)
        except TimeoutException:
            pass

        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "listAreaLi")))

        print(f"成功發起搜尋：{keyword}")

    except Exception as e:
        print(f"搜尋過程中發生錯誤: {e}")


def get_data(driver):
    wait = WebDriverWait(driver, 10)
    items = []
    seen_product_urls = set()

    try:
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "listAreaLi")))
        xpath_str = "//li[contains(@class, 'listAreaLi') and not(.//div[contains(@class, 'sponsor-tag')])]"
        elements = driver.find_elements(By.XPATH, xpath_str)

        print(f"共 {len(elements)} 個非廣告商品")

        for index, el in enumerate(elements):
            try:
                # 商品連結
                product_element = el.find_element(
                    By.CSS_SELECTOR, "div.goods-img-url > a"
                )
                product_url = product_element.get_attribute("href")

                # 圖片連結
                picture_element = el.find_element(By.CSS_SELECTOR, "img.goods-img")
                picture_url = picture_element.get_attribute("src")

                # 品名
                product_name_element = el.find_element(
                    By.CSS_SELECTOR, "h3.prdName > a"
                )
                product_name = product_name_element.text

                # 價格
                sales_price_element = el.find_element(By.CSS_SELECTOR, ".price > b")
                sales_price = sales_price_element.text

                # 店家

                if (
                    product_url
                    and product_url.startswith("http")
                    and picture_url
                    and picture_url.startswith("http")
                ):
                    # 只用 product_url 去重，避免商品和圖片錯位
                    if product_url not in seen_product_urls:
                        seen_product_urls.add(product_url)
                        items.append(
                            {
                                "number": index + 1,
                                "product_name": product_name,
                                "sales_price": sales_price,
                                "store": "momo購物網",
                                "product_url": product_url,
                                "picture_url": picture_url,
                            }
                        )

            except Exception as e:
                print(f"某商品資料抓取失敗: {e}")
                continue

    except Exception as e:
        print(f"抓取商品資料時發生錯誤: {e}")

    return items

    # def get_product_details(driver, product_url, picture_url, index):
    wait = WebDriverWait(driver, 5)
    product_data = {
        "number": index + 1,
        "product_name": "",
        "sales_price": "",
        "store": "",
        "product_url": product_url,
        "picture_url": picture_url,
    }

    # 記錄主分頁
    main_window = driver.current_window_handle

    # 開啟並切換到新分頁
    driver.execute_script("window.open('about:blank', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])

    try:
        driver.get(product_url)
        # 等待品名出現作為載入指標
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)  # 給網頁一點渲染時間

        # 品名
        # 優先找 Meta，再找網頁 ID
        meta_titles = driver.find_elements(By.CSS_SELECTOR, "meta[property='og:title']")
        if meta_titles and meta_titles[0].get_attribute("content"):
            raw_meta_title = meta_titles[0].get_attribute("content")
            product_data["product_name"] = raw_meta_title.split(" - ")[0].strip()
        else:
            name_els = driver.find_elements(
                By.CSS_SELECTOR, "#osmGoodsName, #goods-detail-goods-title, .goodsName"
            )
            if name_els:
                raw_name = name_els[0].text
                product_data["product_name"] = raw_name.split(" - ")[0].strip()

        # 價格
        meta_prices = driver.find_elements(
            By.CSS_SELECTOR, 'meta[property="product:price:amount"]'
        )
        if meta_prices and meta_prices[0].get_attribute("content"):
            product_data["sales_price"] = meta_prices[0].get_attribute("content")
        else:
            price_els = driver.find_elements(
                By.CSS_SELECTOR, "span.seoPrice, .productPrice, span.text-ec_4xl"
            )
            if price_els:
                product_data["sales_price"] = price_els[0].text

        # 商店
        meta_stores = driver.find_elements(By.CSS_SELECTOR, 'meta[name="Author"]')
        if meta_stores and meta_stores[0].get_attribute("content"):
            product_data["store"] = meta_stores[0].get_attribute("content")
        else:
            store_els = driver.find_elements(
                By.CSS_SELECTOR, "a.store-header-logo-box, .brandName"
            )
            if store_els:
                # 優先抓 title 屬性，抓不到再抓 text
                product_data["store"] = (
                    store_els[0].get_attribute("title") or store_els[0].text
                )

    except Exception as e:
        print(f"抓取失敗: {driver.current_url} | 錯誤: {e}")

    finally:
        # 3. 關閉分頁並切回主頁
        driver.close()
        driver.switch_to.window(main_window)
    return product_data


def go_to_next_page(driver):
    wait = WebDriverWait(driver, 10)

    try:
        # 先記錄目前第一個商品的網址
        first_link_el = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "li.listAreaLi div.goods-img-url > a")
            )
        )
        old_first_href = first_link_el.get_attribute("href")

        next_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.page-btn.page-next > a"))
        )

        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", next_btn
        )
        time.sleep(1)

        try:
            next_btn.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", next_btn)

        # 等到第一個商品網址改變，代表真的換頁
        wait.until(
            lambda d: d.find_element(
                By.CSS_SELECTOR, "li.listAreaLi div.goods-img-url > a"
            ).get_attribute("href")
            != old_first_href
        )

        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "listAreaLi")))

        print("成功翻到下一頁")
        return True

    except Exception as e:
        print(f"翻頁失敗或已無下一頁: {e}")
        return False


def save_to_json(data, filename):
    """將結果存成 JSON 檔"""
    try:
        # ensure_ascii=False 正常顯示中文
        # indent=4 排版
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"JSON 儲存成功：{filename}")
    except Exception as e:
        print(f"JSON 儲存失敗：{e}")


def main():
    driver = None

    while True:
        keyword = input("請輸入關鍵字: ").strip()
        if keyword:
            break
        else:
            print("關鍵字不能為空, 請重新輸入: ")

    while True:
        page_input = input("請輸入要爬幾頁（1~5）: ").strip()
        try:
            max_pages = int(page_input)
            if 1 <= max_pages <= 5:
                break
            else:
                print("頁數必須介於 1 到 5 之間，請重新輸入。")
        except ValueError:
            print("請輸入有效的整數頁數。")

    try:
        driver = create_driver()
        # A. 啟動並前往官網
        url = "https://www.momoshop.com.tw/main/Main.jsp"
        driver.get(url)

        # A.1. 設定等待時間
        wait = WebDriverWait(driver, 10)
        close_ad_overlay(driver, wait)

        # B. 搜尋關鍵字
        search_product(driver, keyword)

        # C. 取得搜尋商品所有網址（多頁）
        all_items = []

        for page in range(max_pages):
            print(f"\n--- 正在抓第 {page + 1} 頁 ---")

            print("準備執行 get_urls()")
            items = get_data(driver)
            print(f"get_data() 抓到 {len(items)} 筆")

            all_items.extend(items)

            # 如果不是最後一頁，就翻頁
            if page < max_pages - 1:
                print("準備翻到下一頁...")
                success = go_to_next_page(driver)
                print(f"go_to_next_page() 回傳: {success}")

                if not success:
                    print("沒有下一頁了，提前結束")
                    break

                time.sleep(random.uniform(2, 4))

        # 去重（用 product_url）
        seen = set()
        unique_items = []

        for item in all_items:
            if item["product_url"] not in seen:
                seen.add(item["product_url"])
                unique_items.append(item)

        items = unique_items

        print(f"\n總共抓到 {len(items)} 筆商品")

        # E. 儲存結果
        if items:
            # 重新整理編號 (Number)，確保從 1 到 N 排序，不會每頁都從 1 開始
            for idx, item in enumerate(items, 1):
                item["number"] = idx

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # 建立資料夾
            folder_name = "scraping_data"
            os.makedirs(folder_name, exist_ok=True)

            # 儲存路徑 (檔名加上關鍵字與時間戳)
            base_path = os.path.join(folder_name, f"momo_{keyword}_{timestamp}")
            print(f"\n--- 開始儲存資料 (共 {len(items)} 筆) ---")

            # 執行儲存
            save_to_json(items, f"{base_path}.json")

            print(f"檔案已儲存至: {base_path}.json")
            print("--- 所有檔案儲存完畢 ---\n")
        else:
            print("未抓取到任何資料，不執行儲存。")

    except Exception as e:
        print(f"程式執行過程中發生錯誤: {e}")

    finally:
        # 關閉瀏覽器
        if driver:
            driver.quit()


if __name__ == "__main__":
    main()
