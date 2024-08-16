import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException
import time
import os


# 从API获取Excel文件和文件名
def get_excel_and_filename(api_url):
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        excel_content = requests.get(data['excel_url']).content
        excel_filename = data['filename']

        # 保存Excel文件
        file_path = os.path.join(os.getcwd(), excel_filename)
        with open(file_path, 'wb') as f:
            f.write(excel_content)

        return file_path, excel_filename
    else:
        raise Exception("Failed to retrieve data from API")


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
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.ID, "transmitButton"))
    )
    driver.find_element(By.ID, "overlayCloseLnkId").click()
    return {"message": "success", "screenshot": None}


# 检查反馈
def check_responses(driver):
    driver.find_element(By.ID, "responseButton").click()
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div img[src='/static/roundErrorBullet.gif']"))
    )
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


# 创建Type 86条目
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
        success_message = WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'entries were created')]"))
        )
        driver.save_screenshot("success_message_screenshot.png")
        return {"message": "success: " + success_message.text, "screenshot": "success_message_screenshot.png"}
    except TimeoutException:
        driver.save_screenshot("timeout_error_screenshot.png")
        return {"message": "error: progress bar or success message not found",
                "screenshot": "timeout_error_screenshot.png"}


# 返回结果到API
def return_results_to_api(api_url, results):
    response = requests.post(api_url, json=results)
    return response.status_code == 200


def main():
    api_url = "https://example.com/api/get_excel"  # 替换为获取Excel的API URL
    return_api_url = "https://example.com/api/return_results"  # 替换为返回结果的API URL

    driver = webdriver.Chrome()
    driver.maximize_window()

    try:
        file_path, filename = get_excel_and_filename(api_url)
        login(driver)
        navigate_to_upload_page(driver)
        upload_excel(driver, file_path)
        wait_for_upload_and_click_link(driver, filename)

        result_ams = transmit_ams_acas(driver)
        if result_ams['message'].startswith("error"):
            return_results_to_api(return_api_url, result_ams)
            print(result_ams['message'])
            return

        result_responses = check_responses(driver)
        if result_responses['message'].startswith("error"):
            return_results_to_api(return_api_url, result_responses)
            print(result_responses['message'])
            return

        result_create = create_type_86_entry(driver)
        return_results_to_api(return_api_url, result_create)
        print(result_create['message'])

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
