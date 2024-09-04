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
from threading import Lock


# Function to create a new directory for each excel_filename
def create_directory_for_excel(excel_filename):
    dir_path = os.path.join(os.getcwd(), excel_filename)
    print(dir_path)
    if os.path.exists(dir_path):
        # If directory exists, take a screenshot and return an error message
        # screenshot_path = os.path.join(os.getcwd(), f"{excel_filename}_directory_exists.png")
        # driver.save_screenshot(screenshot_path)
        return {"message": "error: Already been pushed before", "dir_path": dir_path}
    else:
        # Create directory if it does not exist
        os.makedirs(dir_path)
        return {"message": "success", "dir_path": dir_path}

# Function to save screenshot in the created directory
def save_screenshot(driver, screenshot_name, dir_path):
    screenshot_path = os.path.join(dir_path, screenshot_name)
    driver.save_screenshot(screenshot_path)
    return screenshot_path

def get_actual_download_url(file_url):
    """
    This function constructs the API URL to retrieve the actual download URL for the file.
    """
    preview_api_base_url = "https://admin.tolead.com/adminapi/s3file/preview"
    full_api_url = f"{preview_api_base_url}?fileName={file_url}"

    response = requests.post(full_api_url)

    if response.status_code == 200:
        response_data = response.json()
        if response_data.get("status") and response_data.get("code") == 200:
            return response_data.get("data")  # Get the actual download URL from 'data' field
        else:
            print(f"Error in response: {response_data.get('message')}")
    else:
        print(f"Failed to get download URL for {file_url}: {response.text}")

    return None

# Function to get data from the API
def get_data_from_api(api_url):
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        if data['status'] and data['data']:
            records = data['data']  # Get the list of records
            data_list = []

            for record in records:
                file_url = record['fileUrl']
                excel_filename = record['mawbNo']
                record_id = record['id']
                data_list.append({
                    'file_url': file_url,
                    'excel_filename': excel_filename,
                    'record_id': record_id
                })

            return data_list
        else:
            print("No data available.")
            return []  # Return an empty list when no data is available
    else:
        print("Failed to retrieve data from API.")
        return []  # Return an empty list if the request failed


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

def wait_for_upload_and_click_link(driver, partial_filename, dir_path):
    try:
        # Initialize WebDriverWait
        wait = WebDriverWait(driver, 600)  # Set timeout duration

        while True:
            # Check if the error message is present
            error_divs = driver.find_elements(By.XPATH, "//div[img[@src='/static/roundErrorBullet.gif']]")
            if error_divs:
                error_message = error_divs[0].text.strip()
                if "The data could not be uploaded" in error_message:
                    # Take a screenshot and return an error message if the specific error message is found
                    screenshot_path = save_screenshot(driver, "upload_error_screenshot.png", dir_path)
                    return {"message": f"error: {error_message}", "screenshot": screenshot_path}
            else:
                # Check if the upload link is present
                try:
                    upload_link = wait.until(
                        EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, partial_filename))
                    )
                    if upload_link:
                        # Click the upload link if no error is found
                        upload_link.click()
                        return {"message": "success", "screenshot": None}

                except TimeoutException:
                    # If the upload link is not found within the specified wait time, continue the loop to check again
                    continue

            # Brief sleep to prevent busy-waiting and to give time for the page to update
            time.sleep(1)

    except TimeoutException:
        # Handle timeout exception if the upload link or error message does not appear in the specified time
        screenshot_path = save_screenshot(driver, "upload_link_timeout_error.png", dir_path)
        return {"message": "error: timeout waiting for upload link or error message", "screenshot": screenshot_path}

# 921 edit
# Function to edit MAWB if excel_filename starts with "921"
def edit_mawb_if_needed(driver, excel_filename, dir_path):
    if excel_filename.startswith("921"):
        try:
            # Navigate to the "Edit MAWB" page
            edit_mawb_link = driver.find_element(By.XPATH, f"//a[contains(@href, '/app/ams/editMawb.do?amsMawbId=')]")
            edit_mawb_link.click()

            # Clear the input fields for "importingCarrier" and "flightNo"
            importing_carrier_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "impC"))
            )
            importing_carrier_input.clear()

            flight_no_input = driver.find_element(By.ID, "fln")
            flight_no_input.clear()

            # Click the "Save Changes" button
            save_changes_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Save Changes']")
            save_changes_button.click()

            print("MAWB edited successfully.")

        except Exception as e:
            # Handle exceptions such as missing elements or timeout
            screenshot_path = save_screenshot(driver, "edit_mawb_error_screenshot.png", dir_path)
            print(f"Error while editing MAWB: {e}")
            return {"message": "error: failed to edit MAWB", "screenshot": screenshot_path}

    # Return success if no edit was needed or editing was successful
    return {"message": "success", "screenshot": None}

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
    time.sleep(5)
    select = Select(driver.find_element(By.ID, "disFwsR"))
    time.sleep(2)
    select.select_by_value("E")
    time.sleep(2)
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
        # success_message = WebDriverWait(driver, 1000).until(
        #     EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'entries were created')]"))
        # )
        # screenshot_path = save_screenshot(driver, "success_message_screenshot.png", dir_path)
        # return {"message": "success: " + success_message.text, "screenshot": screenshot_path}

        # Wait for any of the success conditions to be true
        WebDriverWait(driver, 1000).until(
            lambda d: (
                    any("Queued" in elem.text for elem in
                        d.find_elements(By.XPATH, "//*[starts-with(@id, 'queued')]")) or
                    any("%" in elem.text and int(elem.text.strip('%')) > 0 for elem in
                        d.find_elements(By.XPATH, "//*[contains(text(), '%')]")) or
                    d.find_element(By.XPATH, "//*[contains(text(),'entries were created')]")
            )
        )

        # Once any condition is met, take a screenshot and return a success message
        screenshot_path = save_screenshot(driver, "success_screenshot.png", dir_path)
        return {"message": "success", "screenshot": screenshot_path}
    except TimeoutException:
        screenshot_path = save_screenshot(driver, "timeout_error_screenshot.png", dir_path)
        return {"message": "error: success message not found",
                "screenshot": screenshot_path}


def check_admissible(excel_filename, dir_path, processed_set):
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

        # If there are multiple search results, click the last one
        if len(search_results) > 1:
            print(f"Multiple search results found: {len(search_results)}. Clicking on the last one.")
            search_results[-1].click()  # Click on the last search result
        elif len(search_results) == 1:
            print("Only one search result found. Clicking on it.")
            search_results[0].click()  # Click the only search result
        else:
            # If no search results are found, return an error
            screenshot_path = save_screenshot(driver, "no_search_results_error.png", dir_path)
            return {
                "message": "error: no search results found, unable to proceed",
                "screenshot": screenshot_path
            }

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
            processed_set.add(excel_filename)
            return {"message": "success: entry is admissible", "screenshot": screenshot_path}
        else:
            screenshot_path = save_screenshot(driver, "not_admissible_error.png", dir_path)
            return {"message": "error: not admissible", "screenshot": screenshot_path}
    except TimeoutException:
        screenshot_path = save_screenshot(driver, "timeout_error_admissible_check.png", dir_path)
        return {"message": "error: timeout waiting for admissible text",
                "screenshot": screenshot_path}


# Function to handle browser automation with Selenium
def perform_browser_operations(excel_filename, file_path, record_id, current_checklist):
    result_excel = create_directory_for_excel(excel_filename)
    if result_excel['message'] == 'error: Already been pushed before':
        if (excel_filename, record_id) not in current_checklist:
            current_checklist.append((excel_filename, record_id))
            return {"message": "Added to list", "screenshot": None}
        else:
            return {"message": "Already in list", "screenshot": None}
    else:
        dir_path = result_excel['dir_path']
        driver = webdriver.Chrome()
        driver.maximize_window()

        try:
            login(driver)
            navigate_to_upload_page(driver)
            upload_excel(driver, file_path)

            result_upload = wait_for_upload_and_click_link(driver, excel_filename, dir_path)
            if result_upload['message'].startswith("error"):
                return result_upload

            result_edit = edit_mawb_if_needed(driver, excel_filename, dir_path)
            if result_edit['message'].startswith("error"):
                return result_edit

            result_ams = transmit_ams_acas(driver, dir_path)
            if result_ams['message'].startswith("error"):
                return result_ams

            result_responses = check_responses(driver, dir_path)
            if result_responses['message'].startswith("error"):
                return result_responses

            result_create = create_type_86_entry(driver, dir_path)
            if result_create['message'].startswith("error"):
                return result_create

            return {"message": "success", "screenshot": None}

        finally:
            # Ensure driver is always quit after operations
            driver.quit()


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

    # Prepare the request payloadt
    payload = {
        "appKey": app_key,
        "file": file_data,
        "sign": sign_16,
        "timeStamp": timestamp
    }

    # Send POST request to the S3 upload API
    url = "https://admin.tolead.com/adminapi/s3file/uploadByAppkey"
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
    print(data)
    if response.status_code == 200:
        print("Results sent successfully!")
        return True
    else:
        print("Failed to send results. HTTP Status:", response.status_code)
        return False

# Initialize a lock
checklist_lock = Lock()

def periodic_check(current_checklist, return_api_url, processed_set):
    while True:
        current_time = datetime.now()
        if current_time.minute == 57:  # Execute at the specified time, e.g., every hour at 0 minutes
            print("Processing the current checklist...")

            for _ in range(len(current_checklist)):
                with checklist_lock:  # Acquire lock before modifying shared resources
                    if not current_checklist:
                        break  # Exit if the checklist is empty, although in this case it will not happen
                    excel_filename, record_id = current_checklist.pop(0)  # Pop the first item safely

                # Process the popped item outside the lock to minimize lock contention
                print(excel_filename, record_id)
                dir_path = os.path.join(os.getcwd(), excel_filename)
                result = check_admissible(excel_filename, dir_path, processed_set)
                return_results_to_api(return_api_url, record_id, excel_filename, result['message'],
                                      result['screenshot'])

            print("Checklist processing complete!")

        time.sleep(60)  # Wait for 60 seconds before checking again


def add_to_current_checklist(current_checklist, new_entry):
    with checklist_lock:  # Acquire lock before modifying shared resources
        current_checklist.append(new_entry)  # Safely add new entries


# Main process
def main_process(current_checklist, processed_set, api_url, return_api_url):
    while True:
        # Get data list from the API
        data_list = get_data_from_api(api_url)
        print(data_list)

        if data_list:
            for data in data_list:
                file_url, excel_filename, record_id = data['file_url'], data['excel_filename'], data['record_id']
                print(f"Data retrieved for MAWB No: {excel_filename}. Processing...")
                print(file_url, excel_filename, record_id)

                if file_url and excel_filename and record_id:
                    # Get actual download URL using file_url as randomName
                    actual_download_url = get_actual_download_url(file_url)
                    print(actual_download_url, excel_filename, record_id)

                    if actual_download_url and excel_filename not in processed_set:
                        try:
                            print(f"Processing data for MAWB No: {excel_filename}...")
                            file_path = download_excel(actual_download_url, excel_filename)
                            result = perform_browser_operations(excel_filename, file_path, record_id, current_checklist)
                            return_results_to_api(return_api_url, record_id, excel_filename, result['message'],
                                                  result['screenshot'])
                            if not result['message'].startswith("error"):
                                current_checklist.append((excel_filename, record_id))
                        except Exception as e:
                            print(f"An error occurred: {e}")
                else:
                    print("Invalid data. Skipping this record.")
        else:
            print("No data to process.")
            print("Sleeping for 30 minutes...")
            time.sleep(1800)  # 30 minutes sleep


# Main function to run both tasks concurrently and manage checklist switching
def main():
    api_url = "https://us-cbsapi.tolead.com/t86CustomsClearanceNetchb/queryList"
    return_api_url = "https://us-cbsapi.tolead.com/t86CustomsClearanceNetchb/netchbConfrim"

    current_checklist = []  # Checklist for the current hour
    processed_set = set()  # Set to track processed or in-progress master numbers

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(main_process, current_checklist, processed_set, api_url, return_api_url)
        executor.submit(periodic_check, current_checklist, return_api_url, processed_set)

if __name__ == "__main__":
    main()
