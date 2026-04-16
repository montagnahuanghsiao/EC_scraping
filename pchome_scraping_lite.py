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
            EC.presence_of_element_located((By.CSS_SELECTOR, "input.c-search__input"))
        )

        # 2. 清空並輸入關鍵字
        product_search.clear()
        product_search.send_keys(keyword)

        # 3. 等待搜尋按鈕可以被點擊，然後點下去
        search_btn = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button[data-regression='header_search_button']")
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
                    (By.CSS_SELECTOR, "button[data-regression='header_search_button']")
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

        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".c-listInfoGrid__body"))
        )

        print(f"成功發起搜尋：{keyword}")

    except Exception as e:
        print(f"搜尋過程中發生錯誤: {e}")


def get_data(driver):
    wait = WebDriverWait(driver, 10)
    items = []
    seen_product_urls = set()

    try:
        # 1. 等待商品容器出現
        wait.until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    ".c-listInfoGrid__list.c-listInfoGrid__list--wrapProdCard",
                )
            )
        )

        # 取得目前頁面總高度
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            # 每次捲動一個視窗高度
            driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(0.6)  # 停留時間稍長，確保請求發出
            new_height = driver.execute_script("return document.body.scrollHeight")
            # 視窗位置
            curr_pos = driver.execute_script(
                "return window.pageYOffset + window.innerHeight"
            )
            if curr_pos >= new_height:  # 捲到底部
                break

        # 3. 抓取所有商品元素 (排除廣告)
        # 使用 :not(:has(...)) 排除帶有廣告標籤的項目
        elements = driver.find_elements(
            By.CSS_SELECTOR,
            "li.c-listInfoGrid__item.c-listInfoGrid__item--gridCardGray5Rwd:not(:has(.c-label__rectangle--frosted))",
        )

        print(f"PCHOME: 共 {len(elements)} 個非廣告商品")

        for index, el in enumerate(elements):
            try:
                # --- 提取資料 ---
                # A. 連結與品名
                product_element = el.find_element(
                    By.CSS_SELECTOR, "div.c-prodInfoV2.c-prodInfoV2--gridCard > a"
                )
                product_url = product_element.get_attribute("href")
                raw_name = product_element.text
                clean_name = raw_name.split(" - ")[0].strip()

                # B. 圖片 (優先抓 data-src)
                img_el = el.find_element(
                    By.CSS_SELECTOR, "img[data-regression='store_prodImg']"
                )
                picture_url = img_el.get_attribute("data-src") or img_el.get_attribute(
                    "src"
                )

                # C. 價格
                # PCHOME 的價格通常在 .c-prodInfoV2__priceValue
                try:
                    price_el = el.find_element(
                        By.CSS_SELECTOR, ".c-prodInfoV2__priceValue, .price"
                    )
                    sales_price = (
                        price_el.text.replace("$", "").replace(",", "").strip()
                    )
                except:
                    sales_price = "0"

                # --- 驗證與去重 ---
                if (
                    product_url
                    and product_url.startswith("http")
                    and picture_url
                    and not "mobile_loading.svg" in picture_url
                    and product_url not in seen_product_urls
                ):
                    seen_product_urls.add(product_url)
                    items.append(
                        {
                            "number": index + 1,
                            "product_name": clean_name,
                            "sales_price": sales_price,
                            "store": "PChome 24h購物",  # 統一標註
                            "product_url": product_url,
                            "picture_url": picture_url,
                        }
                    )

            except Exception as e:
                # print(f"單筆解析跳過: {e}")
                continue

    except Exception as e:
        print(f"抓取 PCHOME 資料時發生錯誤: {e}")

    return items


def go_to_next_page(driver):
    wait = WebDriverWait(driver, 10)

    try:
        # 先記錄目前第一個商品的網址
        first_link_el = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.c-prodInfoV2.c-prodInfoV2--gridCard > a")
            )
        )
        old_first_href = first_link_el.get_attribute("href")

        next_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "i[class*='arrowSolidRight']"))
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
                By.CSS_SELECTOR, "[data-regression='store_prodImg']"  # 加上中括號
            ).get_attribute("src")
            != old_first_href
        )

        wait.until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    ".c-listInfoGrid__list.c-listInfoGrid__list--wrapProdCard",
                )
            )
        )

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
        url = "https://24h.pchome.com.tw/"
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
            print(f"get_urls() 抓到 {len(items)} 筆")

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
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # 建立資料夾
            folder_name = "scraping_data"
            os.makedirs(folder_name, exist_ok=True)

            # 儲存路徑
            base_path = os.path.join(folder_name, f"PCHOME24_{keyword}_{timestamp}")

            print(f"\n--- 開始儲存資料 (共 {len(items)} 筆) ---")
            save_to_json(items, f"{base_path}.json")
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
