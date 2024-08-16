from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time
from selenium.common.exceptions import TimeoutException


def login(driver):
    driver.get("https://www.netchb.com/app/")
    driver.find_element(By.ID, "lName").send_keys("rwang78")
    driver.find_element(By.ID, "pass").send_keys("Wangruide19960525!")
    driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Login']").click()


def navigate_to_upload_page(driver):
    driver.find_element(By.ID, "amsLink").click()
    driver.find_element(By.LINK_TEXT, "Upload Shipment").click()


def upload_excel(driver, file_path):
    driver.find_element(By.ID, "fl").send_keys(file_path)
    driver.find_element(By.ID, "tHU").click()


def wait_for_upload_and_click_link(driver, partial_filename):
    # Wait until the upload link with the partial filename appears
    upload_link = WebDriverWait(driver, 600).until(
        EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, partial_filename))
    )
    upload_link.click()


def transmit_ams_acas(driver):
    driver.find_element(By.ID, "transmitButton").click()

    # Wait for the pop-up and confirm the selection
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "adrp"))
    )
    select = Select(driver.find_element(By.ID, "adrp"))

    # 检查默认选择的值
    selected_value = select.first_selected_option.get_attribute("value")

    if selected_value == "replace":
        print("错误：发现已选择'Replace'，程序将停止。")
        driver.save_screenshot("error_ams_already_done.png")
        return "error: already done AMS filling"

    # 如果选择的是"add"，继续操作
    select.select_by_value("add")
    driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Transmit']").click()

    # Wait for transmit to reappear
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.ID, "transmitButton"))
    )
    driver.find_element(By.ID, "overlayCloseLnkId").click()

    return "success"


def check_responses(driver):
    driver.find_element(By.ID, "responseButton").click()

    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div img[src='/static/roundErrorBullet.gif']"))
    )

    h_rej = driver.find_element(By.ID, "hRej").text
    a_rej = driver.find_element(By.ID, "aRej").text

    if h_rej != "0" or a_rej != "0":
        driver.save_screenshot("error_screenshot.png")
        return "error"

    driver.refresh()

    ams_status = driver.find_element(By.ID, "amsStatusCell").text
    acas_status = driver.find_element(By.ID, "acasStatusCell").text

    if ams_status == "Accepted" and acas_status == "Accepted":
        driver.save_screenshot("success_screenshot.png")
        return "ams_success"

    return "error"


def create_type_86_entry(driver):
    driver.find_element(By.LINK_TEXT, "Create Type 86 Entries").click()
    driver.find_element(By.ID, "imRec").send_keys("RUIDE")
    driver.find_element(By.ID, "impSearch").click()

    # 获取所有窗口句柄
    all_windows = driver.window_handles
    if len(all_windows) > 1:
        # 切换到新弹出的窗口
        driver.switch_to.window(all_windows[-1])

    try:
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Select"))
        ).click()
    except TimeoutException as e:
        driver.save_screenshot("timeout_error_select_link.png")
        return "error: timeout waiting for Select link"

    driver.switch_to.window(driver.window_handles[0])

    select = Select(driver.find_element(By.ID, "disFwsR"))
    select.select_by_value("E")

    # 提交表单
    driver.find_element(By.ID, "sub").click()

    # 检查是否有错误消息
    try:
        error_message = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".errorClass"))  # 假设错误消息有一个类名 .errorClass
        )
        driver.save_screenshot("error_message_screenshot.png")
        return "error: entry creation failed"
    except TimeoutException:
        pass

    # wait for progress bar
    try:
        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".progressBarClass"))  # 假设进度条有一个类名 .progressBarClass
        )
        print("进度条出现，等待条目创建完成...")

        # 等待成功消息
        success_message = WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'entries were created')]"))
        )
        driver.save_screenshot("success_message_screenshot.png")
        return "success: " + success_message.text

    except TimeoutException:
        driver.save_screenshot("timeout_error_screenshot.png")
        return "error: progress bar or success message not found"


def main():
    driver = webdriver.Chrome()  # 确保安装了正确版本的ChromeDriver
    driver.maximize_window()

    try:
        login(driver)
        navigate_to_upload_page(driver)
        upload_excel(driver, r"C:\Users\nicole6927\Desktop\Descartes_180-27012716_2024-08-15.xlsx")
        wait_for_upload_and_click_link(driver, "180-27012716")

        # 传输 AMS/ACAS 并检查是否存在错误
        result = transmit_ams_acas(driver)
        if result.startswith("error"):
            return

        # 检查反馈，并根据结果处理
        result = check_responses(driver)
        if result.startswith("error"):
            print(result)
            return

        if result == "ams_success":
            create_type_86_entry(driver)
            print("报关流程成功完成")
            # 可以在此处返回或推送成功消息和截图
        else:
            print("报关流程失败，检查反馈")
            # 可以在此处返回或推送错误消息和截图

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
