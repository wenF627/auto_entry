import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException
import asyncio
from datetime import datetime, timedelta
import os
import time


# Async function to get data from the API
async def get_data_from_api(api_url):
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, requests.get, api_url)
    if response.status_code == 200:
        data = response.json()
        if data['status'] and data['data']:
            record = data['data'][0]
            file_url = record['fileUrl']
            excel_filename = record['mawbNo']
            record_id = record['id']
            return file_url, excel_filename, record_id
        else:
            print("No data available.")
            return None, None, None
    else:
        print("Failed to retrieve data from API.")
        return None, None, None


# Synchronous function to download Excel file
def download_excel(file_url, excel_filename):
    response = requests.get(file_url)
    file_path = os.path.join(os.getcwd(), f"{excel_filename}.xlsx")
    with open(file_path, 'wb') as f:
        f.write(response.content)
    return file_path

# 登录功能
def login(driver):
    driver.get("https://www.netchb.com/app/")
    driver.find_element(By.ID, "lName").send_keys("rwang78")
    driver.find_element(By.ID, "pass").send_keys("Wangruide19960525!")
    driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Login']").click()


# 导航到上传页面
def navigate_to_upload_page(driver):
    driver.find_element(By.ID, "amsLink").click()
    driver.find_element(By.LINK_TEXT, "Upload Shipment").click()


# 上传Excel文件
def upload_excel(driver, file_path):
    driver.find_element(By.ID, "fl").send_keys(file_path)
    driver.find_element(By.ID, "tHU").click()


# 等待并点击上传后的链接
def wait_for_upload_and_click_link(driver, partial_filename):
    upload_link = WebDriverWait(driver, 600).until(
        EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, partial_filename))
    )
    upload_link.click()

# 传输AMS/ACAS
def transmit_ams_acas(driver):
    driver.find_element(By.ID, "transmitButton").click()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "adrp"))
    )
    select = Select(driver.find_element(By.ID, "adrp"))
    selected_value = select.first_selected_option.get_attribute("value")
    if selected_value == "replace":
        driver.save_screenshot("error_ams_already_done.png")
        return {"message": "error: already done AMS filling", "screenshot": "error_ams_already_done.png"}
    select.select_by_value("add")
    driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Transmit']").click()
    WebDriverWait(driver, 300).until(
        EC.presence_of_element_located((By.ID, "transmitButton"))
    )
    driver.find_element(By.ID, "overlayCloseLnkId").click()
    return {"message": "success", "screenshot": None}

# 检查反馈
def check_responses(driver):
    print("点击 'Check for Responses' 按钮...")
    driver.find_element(By.ID, "responseButton").click()

    try:
        print("等待页面元素加载...")
        WebDriverWait(driver, 600).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div img[src='/static/roundErrorBullet.gif']"))
        )
        print("元素已加载，继续执行...")
    except TimeoutException as e:
        print("元素加载超时，可能页面未正确加载。")
        driver.save_screenshot("timeout_error_screenshot.png")
        return {"message": "error: element not found", "screenshot": "timeout_error_screenshot.png"}

    h_rej = driver.find_element(By.ID, "hRej").text
    a_rej = driver.find_element(By.ID, "aRej").text

    if h_rej != "0" or a_rej != "0":
        driver.save_screenshot("error_screenshot.png")
        return {"message": "error", "screenshot": "error_screenshot.png"}

    driver.refresh()

    ams_status = driver.find_element(By.ID, "amsStatusCell").text
    acas_status = driver.find_element(By.ID, "acasStatusCell").text

    if ams_status == "Accepted" and acas_status == "Accepted":
        driver.save_screenshot("success_screenshot.png")
        return {"message": "ams_success", "screenshot": "success_screenshot.png"}

    return {"message": "error", "screenshot": None}

def create_type_86_entry(driver):
    driver.find_element(By.LINK_TEXT, "Create Type 86 Entries").click()
    driver.find_element(By.ID, "imRec").send_keys("RUIDE")
    driver.find_element(By.ID, "impSearch").click()
    all_windows = driver.window_handles
    if len(all_windows) > 1:
        driver.switch_to.window(all_windows[-1])
    try:
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Select"))
        ).click()
    except TimeoutException as e:
        driver.save_screenshot("timeout_error_select_link.png")
        return {"message": "error: timeout waiting for Select link", "screenshot": "timeout_error_select_link.png"}
    driver.switch_to.window(driver.window_handles[0])
    select = Select(driver.find_element(By.ID, "disFwsR"))
    select.select_by_value("E")
    driver.find_element(By.ID, "sub").click()
    try:
        error_message = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".errorClass"))
        )
        driver.save_screenshot("error_message_screenshot.png")
        return {"message": "error: entry creation failed", "screenshot": "error_message_screenshot.png"}
    except TimeoutException:
        pass
    try:
        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".progressBarClass"))
        )
        success_message = WebDriverWait(driver, 600).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'entries were created')]"))
        )
        driver.save_screenshot("success_message_screenshot.png")
        return {"message": "success: " + success_message.text, "screenshot": "success_message_screenshot.png"}
    except TimeoutException:
        driver.save_screenshot("timeout_error_screenshot.png")
        return {"message": "error: progress bar or success message not found",
                "screenshot": "timeout_error_screenshot.png"}

def check_admissible(driver, excel_filename):
    driver.find_element(By.ID, "amsLink").click()
    driver.find_element(By.ID, "usmf").click()
    driver.find_element(By.ID, "mSingle").send_keys(excel_filename)
    driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Update']").click()

    try:
        search_results = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, f"a[href*='/app/ams/mawbMenu.do?amsMawbId=']"))
        )

        # Check if there is more than one search result
        if len(search_results) > 1:
            driver.save_screenshot("multiple_search_results_error.png")
            return {
                "message": "error: multiple search results found, unable to proceed",
                "screenshot": "multiple_search_results_error.png"
            }

        # Click the only search result if it's the correct one
        search_results[0].click()

    except TimeoutException:
        driver.save_screenshot("search_results_timeout_error.png")
        return {
            "message": "error: timeout waiting for search results",
            "screenshot": "search_results_timeout_error.png"
        }

    # 点击随机的条目号码链接
    try:
        random_entry_link = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href*='/app/entry/viewEntry.do?filerCode=']"))
        )
        random_entry_link.click()
    except TimeoutException:
        driver.save_screenshot("error_random_entry_link.png")
        return {"message": "error: timeout waiting for random entry link", "screenshot": "error_random_entry_link.png"}

    # 点击ACE Cargo Release Results链接
    try:
        ace_cargo_link = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "ACE Cargo Release Results"))
        )
        ace_cargo_link.click()
    except TimeoutException:
        driver.save_screenshot("error_ace_cargo_link.png")
        return {"message": "error: timeout waiting for ACE Cargo Release Results link",
                "screenshot": "error_ace_cargo_link.png"}

    # 检查是否显示ADMISSIBLE
    try:
        admissible_text = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//pre[contains(text(),'ADMISSIBLE')]"))
        )
        if "ADMISSIBLE" in admissible_text.text:
            driver.save_screenshot("admissible_success.png")
            return {"message": "success: entry is admissible", "screenshot": "admissible_success.png"}
        else:
            driver.save_screenshot("not_admissible_error.png")
            return {"message": "error: not admissible", "screenshot": "not_admissible_error.png"}
    except TimeoutException:
        driver.save_screenshot("timeout_error_admissible_check.png")
        return {"message": "error: timeout waiting for admissible text",
                "screenshot": "timeout_error_admissible_check.png"}
# Synchronous function to handle browser automation with Selenium
def perform_browser_operations(excel_filename, file_path):
    driver = webdriver.Chrome()
    driver.maximize_window()
    login(driver)
    navigate_to_upload_page(driver)
    upload_excel(driver, file_path)
    wait_for_upload_and_click_link(driver, excel_filename)

    result_ams = transmit_ams_acas(driver)
    if result_ams['message'].startswith("error"):
        driver.quit()
        return result_ams

    result_responses = check_responses(driver)
    if result_responses['message'].startswith("error"):
        driver.quit()
        return result_responses

    result_create = create_type_86_entry(driver)
    if result_create['message'].startswith("error"):
        driver.quit()
        return result_create

    # Additional checks
    time.sleep(300)
    result_admissible = check_admissible(driver, excel_filename)
    driver.quit()
    return result_admissible


# Function to send results back to API
async def return_results_to_api(api_url, record_id, excel_filename, result_message, screenshot_path):
    data = {
        "id": record_id,
        "mawbNo": excel_filename,
        "declareResult": result_message,
        "declareResultUrl": screenshot_path
    }
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, requests.post, api_url, json=data)
    print(data)
    return response.status_code == 200


# Periodic checklist task
async def periodic_check(previous_checklist, processed_set):
    while True:
        current_time = datetime.now()
        if current_time.minute == 0:  # Execute at the start of every hour
            print("Checking the previous hour's checklist...")
            for _ in range(len(previous_checklist)):
                excel_filename = previous_checklist.pop(0)
                result = await asyncio.to_thread(check_admissible, webdriver.Chrome(), excel_filename)
                await return_results_to_api(return_api_url, None, excel_filename, result['message'],
                                            result['screenshot'])
                processed_set.remove(excel_filename)
            print("Checklist check complete!")
        await asyncio.sleep(60)  # Check every minute


# Main async process
async def main_process(current_checklist, processed_set, api_url, return_api_url):
    while True:
        file_url, excel_filename, record_id = await get_data_from_api(api_url)
        if file_url and excel_filename and record_id:
            if excel_filename not in processed_set:
                try:
                    processed_set.add(excel_filename)
                    print(f"Data retrieved for MAWB No: {excel_filename}. Processing...")
                    file_path = download_excel(file_url, excel_filename)
                    result = await asyncio.to_thread(perform_browser_operations, excel_filename, file_path)
                    await return_results_to_api(return_api_url, record_id, excel_filename, result['message'],
                                                result['screenshot'])
                    if not result['message'].startswith("error"):
                        current_checklist.append(excel_filename)
                except Exception as e:
                    print(f"An error occurred: {e}")
        else:
            print("No data to process.")

        print("Sleeping for 30 minutes...")
        await asyncio.sleep(1800)  # 30 minutes sleep


# Main function to run both tasks concurrently and manage checklist switching
async def main():
    api_url = "http://139.224.207.21:8085/t86CustomsClearanceNetchb/queryList"
    return_api_url = "http://139.224.207.21:8085/t86CustomsClearanceNetchb/netchbConfrim"

    current_checklist = []  # Checklist for the current hour
    previous_checklist = []  # Checklist for the previous hour
    processed_set = set()  # Set to track processed or in-progress master numbers

    task1 = asyncio.create_task(main_process(current_checklist, processed_set, api_url, return_api_url))
    task2 = asyncio.create_task(periodic_check(previous_checklist, processed_set))

    start_time = datetime.now()  # Track the start time of the hour

    while True:
        await asyncio.sleep(60)  # Wait 60 seconds before checking time again
        current_time = datetime.now()

        # Check if an hour has passed since the start time
        if current_time - start_time >= timedelta(hours=1):
            print(f"Hour passed. Swapping checklists at {current_time.strftime('%H:%M:%S')}.")

            # Move current to previous and reset current
            previous_checklist.extend(current_checklist)
            current_checklist.clear()

            # Update start time to the current time
            start_time = current_time


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
