import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException
import concurrent.futures
from datetime import datetime, timedelta
import os
import base64
import hashlib
import time


# Function to create a new directory for each excel_filename
def create_directory_for_excel(excel_filename):
    dir_path = os.path.join(os.getcwd(), excel_filename)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path


# Function to save screenshot in the created directory
def save_screenshot(driver, screenshot_name, dir_path):
    screenshot_path = os.path.join(dir_path, screenshot_name)
    driver.save_screenshot(screenshot_path)
    return screenshot_path


# Function to get data from the API
def get_data_from_api(api_url):
    response = requests.get(api_url)
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


# Function to download Excel file
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
def transmit_ams_acas(driver, dir_path):
    driver.find_element(By.ID, "transmitButton").click()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "adrp"))
    )
    select = Select(driver.find_element(By.ID, "adrp"))
    selected_value = select.first_selected_option.get_attribute("value")
    if selected_value == "replace":
        screenshot_path = save_screenshot(driver, "error_ams_already_done.png", dir_path)
        return {"message": "error: already done AMS filling", "screenshot": screenshot_path}
    select.select_by_value("add")
    driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Transmit']").click()
    WebDriverWait(driver, 300).until(
        EC.presence_of_element_located((By.ID, "transmitButton"))
    )
    driver.find_element(By.ID, "overlayCloseLnkId").click()
    return {"message": "success", "screenshot": None}


# 检查反馈
def check_responses(driver, dir_path):
    print("click 'Check for Responses' button...")
    driver.find_element(By.ID, "responseButton").click()

    try:
        print("waiting for the page...")
        WebDriverWait(driver, 600).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div img[src='/static/roundErrorBullet.gif']"))
        )
        print("page shown,continue...")
    except TimeoutException as e:
        print("page not show, time out...")
        screenshot_path = save_screenshot(driver, "timeout_error_screenshot.png", dir_path)
        return {"message": "error: element not found", "screenshot": screenshot_path}

    h_rej = driver.find_element(By.ID, "hRej").text
    a_rej = driver.find_element(By.ID, "aRej").text

    if h_rej != "0" or a_rej != "0":
        screenshot_path = save_screenshot(driver, "error_screenshot.png", dir_path)
        return {"message": "error", "screenshot": screenshot_path}

    driver.refresh()

    ams_status = driver.find_element(By.ID, "amsStatusCell").text
    acas_status = driver.find_element(By.ID, "acasStatusCell").text

    if ams_status == "Accepted" and acas_status == "Accepted":
        screenshot_path = save_screenshot(driver, "success_screenshot.png", dir_path)
        return {"message": "ams_success", "screenshot": screenshot_path}

    return {"message": "error", "screenshot": None}


def create_type_86_entry(driver, dir_path):
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
        screenshot_path = save_screenshot(driver, "timeout_error_select_link.png", dir_path)
        return {"message": "error: timeout waiting for Select link", "screenshot": screenshot_path}
    driver.switch_to.window(driver.window_handles[0])
    select = Select(driver.find_element(By.ID, "disFwsR"))
    select.select_by_value("E")
    driver.find_element(By.ID, "sub").click()
    try:
        error_message = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".errorClass"))
        )
        screenshot_path = save_screenshot(driver, "error_message_screenshot.png", dir_path)
        return {"message": "error: entry creation failed", "screenshot": screenshot_path}
    except TimeoutException:
        pass
    try:
        success_message = WebDriverWait(driver, 1000).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'entries were created')]"))
        )
        screenshot_path = save_screenshot(driver, "success_message_screenshot.png", dir_path)
        return {"message": "success: " + success_message.text, "screenshot": screenshot_path}
    except TimeoutException:
        screenshot_path = save_screenshot(driver, "timeout_error_screenshot.png", dir_path)
        return {"message": "error: success message not found",
                "screenshot": screenshot_path}


def check_admissible(excel_filename, dir_path):
    driver = webdriver.Chrome()
    login(driver)
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
            screenshot_path = save_screenshot(driver, "multiple_search_results_error.png", dir_path)
            return {
                "message": "error: multiple search results found, unable to proceed",
                "screenshot": screenshot_path
            }

        # Click the only search result if it's the correct one
        search_results[0].click()

    except TimeoutException:
        screenshot_path = save_screenshot(driver, "search_results_timeout_error.png", dir_path)
        return {
            "message": "error: timeout waiting for search results",
            "screenshot": screenshot_path
        }

    # 点击随机的条目号码链接
    try:
        random_entry_link = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href*='/app/entry/viewEntry.do?filerCode=']"))
        )
        random_entry_link.click()
    except TimeoutException:
        screenshot_path = save_screenshot(driver, "error_random_entry_link.png", dir_path)
        return {"message": "error: timeout waiting for random entry link", "screenshot": screenshot_path}

    # 点击ACE Cargo Release Results链接
    try:
        ace_cargo_link = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "ACE Cargo Release Results"))
        )
        ace_cargo_link.click()
    except TimeoutException:
        screenshot_path = save_screenshot(driver, "error_ace_cargo_link.png", dir_path)
        return {"message": "error: timeout waiting for ACE Cargo Release Results link",
                "screenshot": screenshot_path}

    # 检查是否显示ADMISSIBLE
    try:
        admissible_text = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//pre[contains(text(),'ADMISSIBLE')]"))
        )
        if "ADMISSIBLE" in admissible_text.text:
            screenshot_path = save_screenshot(driver, "admissible_success.png", dir_path)
            return {"message": "success: entry is admissible", "screenshot": screenshot_path}
        else:
            screenshot_path = save_screenshot(driver, "not_admissible_error.png", dir_path)
            return {"message": "error: not admissible", "screenshot": screenshot_path}
    except TimeoutException:
        screenshot_path = save_screenshot(driver, "timeout_error_admissible_check.png", dir_path)
        return {"message": "error: timeout waiting for admissible text",
                "screenshot": screenshot_path}


# Function to handle browser automation with Selenium
def perform_browser_operations(excel_filename, file_path, dir_path):
    driver = webdriver.Chrome()
    driver.maximize_window()

    login(driver)
    navigate_to_upload_page(driver)
    upload_excel(driver, file_path)
    wait_for_upload_and_click_link(driver, excel_filename)

    result_ams = transmit_ams_acas(driver, dir_path)
    if result_ams['message'].startswith("error"):
        driver.quit()
        return result_ams

    result_responses = check_responses(driver, dir_path)
    if result_responses['message'].startswith("error"):
        driver.quit()
        return result_responses

    result_create = create_type_86_entry(driver, dir_path)
    if result_create['message'].startswith("error"):
        driver.quit()
        return result_create


# Function to upload screenshot to S3 via API
def upload_screenshot_to_s3(file_path):
    # Read the screenshot file and encode it in Base64
    with open(file_path, 'rb') as file:
        file_content = file.read()
        file_base64 = base64.b64encode(file_content).decode('utf-8')

    # API related parameters
    app_key = "eKYIY&2HTgMb@5Ci"
    app_sec_key = "9iq^r15fZJ5jQxsK$7&@7B#5yuM$SlpF"
    timestamp = str(int(time.time()))

    # Prepare file data for API request
    file_data = "data:image/png;base64," + file_base64

    # Generate the signature for the request
    sign_string = app_key + file_data + timestamp + app_sec_key + app_key
    sign = hashlib.md5(sign_string.encode('utf-8')).hexdigest()
    sign_16 = sign[8:24]

    # Prepare the request payload
    payload = {
        "appKey": app_key,
        "file": file_data,
        "sign": sign_16,
        "timeStamp": timestamp
    }

    # Send POST request to the S3 upload API
    url = "http://139.224.207.21:8083/adminapi/s3file/uploadByAppkey"
    response = requests.post(url, json=payload)

    # Handle response
    if response.status_code == 200:
        result = response.json()
        if result.get('status'):
            print("Upload successful! File name:", result['data']['randomName'])
            return result['data']['randomName']  # Return the randomName or S3 key
        else:
            print("Upload failed:", result.get('message'))
            return None
    else:
        print("HTTP Error:", response.status_code)
        return None


# Function to send results back to API
def return_results_to_api(api_url, record_id, excel_filename, result_message, screenshot_path):
    screenshot_s3_key = upload_screenshot_to_s3(screenshot_path)
    print(screenshot_s3_key)
    if not screenshot_s3_key:
        print("Failed to upload screenshot to S3. Not sending results back to API.")
        return False

    data = {
        "id": record_id,
        "mawbNo": excel_filename,
        "declareResult": result_message,
        "declareResultUrl": screenshot_s3_key  # Using S3 key obtained from upload
    }

    response = requests.post(api_url, json=data)

    if response.status_code == 200:
        print("Results sent successfully!")
        return True
    else:
        print("Failed to send results. HTTP Status:", response.status_code)
        return False


# Periodic checklist task
def periodic_check(previous_checklist, processed_set, return_api_url):
    while True:
        current_time = datetime.now()
        if current_time.minute == 0:  # Execute at the specified minute
            print("Checking the previous hour's checklist...")
            for _ in range(len(previous_checklist)):
                excel_filename = previous_checklist.pop(0)
                print(excel_filename)
                dir_path = create_directory_for_excel(excel_filename)
                result = check_admissible(excel_filename, dir_path)
                return_results_to_api(return_api_url, None, excel_filename, result['message'],
                                      result['screenshot'])
            print("Checklist check complete!")
        time.sleep(60)  # Check every minute


# Main process
def main_process(current_checklist, processed_set, api_url, return_api_url):
    while True:
        file_url, excel_filename, record_id = get_data_from_api(api_url)
        print(f"Data retrieved for MAWB No: {excel_filename}. Processing...")
        if file_url and excel_filename and record_id:
            if excel_filename not in processed_set:
                try:
                    print(f"Data retrieved for MAWB No: {excel_filename}. Processing...")
                    file_path = download_excel(file_url, excel_filename)
                    dir_path = create_directory_for_excel(excel_filename)
                    result = perform_browser_operations(excel_filename, file_path, dir_path)
                    processed_set.add(excel_filename)
                    return_results_to_api(return_api_url, record_id, excel_filename, result['message'],
                                          result['screenshot'])
                    if not result['message'].startswith("error"):
                        current_checklist.append(excel_filename)
                except Exception as e:
                    print(f"An error occurred: {e}")

        else:
            print("No data to process.")
            print("Sleeping for 30 minutes...")
            time.sleep(1800)  # 30 minutes sleep


# Main function to run both tasks concurrently and manage checklist switching
def main():
    api_url = "http://139.224.207.21:8085/t86CustomsClearanceNetchb/queryList"
    return_api_url = "http://139.224.207.21:8085/t86CustomsClearanceNetchb/netchbConfrim"

    current_checklist = []  # Checklist for the current hour
    previous_checklist = []  # Checklist for the previous hour
    processed_set = set()  # Set to track processed or in-progress master numbers

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(main_process, current_checklist, processed_set, api_url, return_api_url)
        executor.submit(periodic_check, previous_checklist, processed_set, return_api_url)

if __name__ == "__main__":
    main()
