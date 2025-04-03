#!/usr/bin/env python3
import os
import sys
import subprocess
import re
import time
import random
import string
import tempfile
import json
import requests
import zipfile
import imaplib
import email as em
import threading
from faker import Faker
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ---------------------- Cài đặt các gói cần thiết ----------------------
def install_packages():
    packages = {
        "selenium": "selenium==4.9.1",  # ép phiên bản theo hướng dẫn
        "faker": "faker",
        "webdriver-manager": "webdriver-manager",
        "requests": "requests",
        "pysocks": "pysocks"
    }
    for pkg, install_name in packages.items():
        try:
            __import__(pkg)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", install_name])
install_packages()

# ---------------------- Cấu hình delay và các biến global ----------------------
PAGE_LOAD_DELAY = 3
WAIT_TIME_URL_CHANGE = 1
fake = Faker()

# Yêu cầu chọn chế độ đăng ký: "phone" hoặc "email"
SIGNUP_MODE = None
while SIGNUP_MODE not in ["phone", "email"]:
    SIGNUP_MODE = input("Nhập chế độ đăng ký (phone/email): ").strip().lower()

# ---------------------- Tải danh sách tên từ GitHub ----------------------
BOY_NAMES_URL = "https://raw.githubusercontent.com/duyet/vietnamese-namedb/refs/heads/master/boy.txt"
BOY_NAMES_FILE = "boy.txt"

def download_names_file():
    if not os.path.exists(BOY_NAMES_FILE):
        try:
            print("Downloading boy.txt từ GitHub...")
            r = requests.get(BOY_NAMES_URL, timeout=10)
            if r.status_code == 200:
                with open(BOY_NAMES_FILE, "w", encoding="utf-8") as f:
                    f.write(r.text)
                print("Đã tải boy.txt thành công.")
            else:
                print("Lỗi tải boy.txt, status code:", r.status_code)
        except Exception as e:
            print("Lỗi tải boy.txt:", e)

def load_names():
    download_names_file()
    names = []
    if os.path.exists(BOY_NAMES_FILE):
        with open(BOY_NAMES_FILE, "r", encoding="utf-8") as f:
            for line in f:
                name = line.strip()
                if name:
                    names.append(name)
    return names

global_names = load_names()
def get_random_name():
    if global_names:
        full = random.choice(global_names)
        parts = full.split()
        if len(parts) >= 2:
            return parts[0], " ".join(parts[1:])
        else:
            return parts[0], fake.last_name()
    else:
        return fake.first_name(), fake.last_name()

# ---------------------- Hàm tạo email ngẫu nhiên ----------------------
def generate_random_email():
    local = "".join(random.choices(string.ascii_lowercase + string.digits, k=20))
    return local + "@gmail.com"

# ---------------------- Các hàm xử lý số điện thoại ----------------------
def load_trash_numbers():
    if os.path.exists("trash.txt"):
        with open("trash.txt", "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_to_trash(phone):
    with open("trash.txt", "a") as f:
        f.write(phone + "\n")
    print(f"Saved {phone} to trash.txt")

def generate_thai_phone_number():
    phone = "+66" + "8" + "".join(random.choices(string.digits, k=8))
    trash = load_trash_numbers()
    while phone in trash:
        phone = "+66" + "8" + "".join(random.choices(string.digits, k=8))
    return phone

def generate_vietnam_phone_number():
    phone = "+8490" + "".join(random.choices(string.digits, k=7))
    trash = load_trash_numbers()
    while phone in trash:
        phone = "+8490" + "".join(random.choices(string.digits, k=7))
    return phone

def generate_philippines_phone_number():
    phone = "+63917" + "".join(random.choices(string.digits, k=7))
    trash = load_trash_numbers()
    while phone in trash:
        phone = "+63917" + "".join(random.choices(string.digits, k=7))
    return phone

def generate_malaysia_phone_number():
    phone = "+6012" + "".join(random.choices(string.digits, k=7))
    trash = load_trash_numbers()
    while phone in trash:
        phone = "+6012" + "".join(random.choices(string.digits, k=7))
    return phone

def increment_thai_phone(phone):
    if not phone.startswith("+") or len(phone) < 8:
        return phone
    lst = list(phone)
    pos = 7
    carry = 1
    i = pos
    while i >= 1 and carry:
        if lst[i].isdigit():
            s = int(lst[i]) + carry
            lst[i] = str(s % 10)
            carry = 1 if s >= 10 else 0
        i -= 1
    return "".join(lst)

def increment_other_phone(phone):
    if not phone.startswith("+") or len(phone) < 11:
        return phone
    lst = list(phone)
    pos = 10
    carry = 1
    i = pos
    while i >= 1 and carry:
        if lst[i].isdigit():
            s = int(lst[i]) + carry
            lst[i] = str(s % 10)
            carry = 1 if s >= 10 else 0
        i -= 1
    return "".join(lst)

def increment_phone_number(phone, country):
    if country == "thai":
        return increment_thai_phone(phone)
    return increment_other_phone(phone)

country_list = ["thai", "vietnam", "philippines", "malaysia"]
current_country_index = 0
phone_attempt_counter = 0

def get_phone_number():
    global phone_attempt_counter, current_country_index
    country = country_list[current_country_index]
    if country == "thai":
        phone = generate_thai_phone_number()
    elif country == "vietnam":
        phone = generate_vietnam_phone_number()
    elif country == "philippines":
        phone = generate_philippines_phone_number()
    elif country == "malaysia":
        phone = generate_malaysia_phone_number()
    phone_attempt_counter += 1
    if phone_attempt_counter % 50 == 0:
        current_country_index = (current_country_index + 1) % len(country_list)
        print("Chuyển sang quốc gia:", country_list[current_country_index])
    return phone, country

# ---------------------- Hàm đảm bảo ChromeDriver ARM64 ----------------------
CHROMEDRIVER_PATH = "/data/data/com.termux/files/usr/bin/chromedriver"
# URL mẫu tải ChromeDriver (hãy thay đổi URL này thành URL tải chính xác)
CHROMEDRIVER_DOWNLOAD_URL = "https://example.com/chromedriver_arm64.zip"

def ensure_chromedriver():
    if os.path.exists(CHROMEDRIVER_PATH):
        return CHROMEDRIVER_PATH
    print("Không tìm thấy ChromeDriver phù hợp. Đang tải về...")
    try:
        # Tải file zip
        r = requests.get(CHROMEDRIVER_DOWNLOAD_URL, stream=True, timeout=60)
        if r.status_code != 200:
            print("Lỗi tải ChromeDriver, status code:", r.status_code)
            sys.exit(1)
        tmp_zip = os.path.join(tempfile.gettempdir(), "chromedriver_arm64.zip")
        with open(tmp_zip, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        # Giải nén file zip
        with zipfile.ZipFile(tmp_zip, "r") as zip_ref:
            zip_ref.extractall(tempfile.gettempdir())
        # Giả sử file giải nén có tên "chromedriver" (nếu khác, bạn cần sửa lại)
        extracted_path = os.path.join(tempfile.gettempdir(), "chromedriver")
        if not os.path.exists(extracted_path):
            print("Không tìm thấy file ChromeDriver sau giải nén.")
            sys.exit(1)
        # Di chuyển file đến CHROMEDRIVER_PATH
        os.makedirs(os.path.dirname(CHROMEDRIVER_PATH), exist_ok=True)
        os.replace(extracted_path, CHROMEDRIVER_PATH)
        # Cho phép chạy
        os.chmod(CHROMEDRIVER_PATH, 0o755)
        print("ChromeDriver đã được tải và cài đặt tại:", CHROMEDRIVER_PATH)
        return CHROMEDRIVER_PATH
    except Exception as e:
        print("Lỗi khi tải ChromeDriver:", e)
        sys.exit(1)

# ---------------------- Cấu hình Chrome và hàm hỗ trợ ----------------------
def configure_chrome_options(proxy=None, proxy_protocol=None):
    options = Options()
    # Sử dụng chế độ headless mới (theo hướng dẫn của kho Selenium-On-Termux-Android)
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Tạo thư mục user-data tạm thời
    profile = tempfile.mkdtemp()
    options.add_argument(f"--user-data-dir={profile}")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--window-size=1920,1080")
    if proxy and proxy_protocol:
        options.add_argument(f'--proxy-server={proxy_protocol}://{proxy}')
    # Kiểm tra đường dẫn binary của Chromium
    chrome_bin = "/data/data/com.termux/files/usr/bin/chromium"
    if not os.path.exists(chrome_bin):
        chrome_bin = "/data/data/com.termux/files/usr/bin/chromium-browser"
    if os.path.exists(chrome_bin):
        options.binary_location = chrome_bin
    else:
        print("Không tìm thấy Chromium trên Termux!")
        sys.exit(1)
    return options

def remove_browser_warning(driver):
    try:
        script = """
        var el = document.querySelector('span.pts.fsl.fwb');
        if(el && el.textContent.includes('supported browser')) {
            el.parentNode.removeChild(el);
            return true;
        }
        return false;
        """
        res = driver.execute_script(script)
        if res:
            print("Browser warning removed.")
    except Exception as e:
        print("Error removing browser warning:", e)

def check_and_accept_cookies(driver):
    try:
        driver.execute_script("document.body.click();")
    except Exception as e:
        print("Cookie click error:", e)

# ---------------------- Điền form đăng ký ----------------------
def fill_registration_form(driver, wait, skip_cookies, phone_override=None, country_override=None):
    driver.get("https://www.facebook.com/r.php?entry_point=login")
    time.sleep(PAGE_LOAD_DELAY)
    remove_browser_warning(driver)
    if not skip_cookies:
        check_and_accept_cookies(driver)

    # 1) Nhập DOB
    birth_day = str(random.randint(1,28))
    birth_month = str(random.randint(1,12))
    birth_year = str(random.randint(1980,2005))
    try:
        day_elem = wait.until(EC.visibility_of_element_located((By.NAME, 'birthday_day')))
        month_elem = wait.until(EC.visibility_of_element_located((By.NAME, 'birthday_month')))
        year_elem = wait.until(EC.visibility_of_element_located((By.NAME, 'birthday_year')))
        try:
            Select(day_elem).select_by_value(birth_day)
            Select(month_elem).select_by_value(birth_month)
            try:
                Select(year_elem).select_by_value(birth_year)
            except:
                Select(year_elem).select_by_visible_text(birth_year)
            print(f"Đã nhập DOB: {birth_day}/{birth_month}/{birth_year}")
        except Exception as e:
            print("Lỗi khi set DOB qua Select:", e)
            driver.execute_script("arguments[0].value=arguments[1];", day_elem, birth_day)
            driver.execute_script("arguments[0].value=arguments[1];", month_elem, birth_month)
            driver.execute_script("arguments[0].value=arguments[1];", year_elem, birth_year)
    except Exception as e:
        print("Không tìm thấy trường DOB:", e)

    # 2) Nhập họ tên từ file boy.txt
    first_name, last_name = get_random_name()
    try:
        first_elem = wait.until(EC.element_to_be_clickable((By.NAME, 'firstname')))
        first_elem.clear()
        first_elem.send_keys(first_name)
        print("Đã nhập first name:", first_name)
    except Exception as e:
        print("Error sending first name:", e)
    try:
        last_elem = driver.find_element(By.NAME, 'lastname')
        last_elem.clear()
        last_elem.send_keys(last_name)
        print("Đã nhập last name:", last_name)
    except Exception as e:
        print("Error sending last name:", e)

    # 3) Nhập số điện thoại hoặc email tùy thuộc vào SIGNUP_MODE
    if SIGNUP_MODE == "email":
        login_input = generate_random_email()
    else:
        if phone_override:
            login_input = phone_override
            country_override = country_override if country_override else "unknown"
        else:
            login_input, country_override = get_phone_number()
    print(f"Thông tin đăng ký: {login_input} ({'email' if SIGNUP_MODE=='email' else 'phone'})")
    inserted = False
    for _ in range(3):
        try:
            field = driver.find_element(By.NAME, 'reg_email__')
            driver.execute_script("arguments[0].value = '';", field)
            field.clear()
            field.send_keys(login_input)
            print("Đã nhập:", login_input)
            inserted = True
            break
        except Exception as e:
            print("Lỗi nhập login, thử lại:", e)
            time.sleep(2)
    if not inserted:
        print("Không thể nhập login sau 3 lần thử.")

    # 4) Nhập mật khẩu ngẫu nhiên
    try:
        fb_pass = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        pass_field = driver.find_element(By.NAME, 'reg_passwd__')
        pass_field.clear()
        pass_field.send_keys(fb_pass)
        print("Đã nhập mật khẩu:", fb_pass)
    except Exception as e:
        print("Lỗi nhập mật khẩu:", e)
        fb_pass = "ErrorPass"

    # 5) Chọn giới tính
    try:
        gender = random.choice(["1", "2"])
        radio = wait.until(EC.element_to_be_clickable((By.XPATH, f"//input[@name='sex' and @value='{gender}']")))
        driver.execute_script("arguments[0].click();", radio)
        print("Đã chọn giới tính:", "Female" if gender=="1" else "Male")
    except Exception as e:
        print("Error selecting gender:", e)

    # 6) Bấm Sign Up
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    try:
        signup = wait.until(EC.element_to_be_clickable((By.NAME, 'websubmit')))
        signup.click()
        print("Đã nhấn nút Sign Up.")
    except Exception as e:
        print("Lỗi khi nhấn Sign Up:", e)
        driver.execute_script("arguments[0].click();", signup)

    reg_data = {
        "login": login_input,
        "fb_pass": fb_pass,
        "mode": SIGNUP_MODE,
        "country": country_override if SIGNUP_MODE=="phone" else "email",
        "birth_day": birth_day,
        "birth_month": birth_month,
        "birth_year": birth_year
    }
    return reg_data

# ---------------------- Hàm chính: tạo account đến confirm ----------------------
def create_account_function1(proxy=None):
    while True:
        options = configure_chrome_options()
        driver = None
        try:
            # Sử dụng ChromeDriver ARM64 được đảm bảo bởi hàm ensure_chromedriver
            chrome_driver_path = ensure_chromedriver()
            driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)
        except Exception as e:
            print("Không thể khởi tạo trình duyệt:", e)
            time.sleep(5)
            continue

        wait = WebDriverWait(driver, 20)
        reg_data = fill_registration_form(driver, wait, skip_cookies=False)
        success = False
        attempts = 0

        while not success and attempts < 25:
            attempts += 1
            print(f"Attempt {attempts} với {reg_data['login']}")
            time.sleep(WAIT_TIME_URL_CHANGE)
            cur_url = driver.current_url
            if "confirmemail.php" in cur_url:
                print("Đã đến màn hình confirm email.")
                success = True
                break
            if "There was an error with your registration" in driver.page_source:
                print("Có lỗi đăng ký. Tăng số điện thoại/email theo quy tắc...")
                new_login = None
                if SIGNUP_MODE == "phone":
                    new_login = increment_phone_number(reg_data["login"], reg_data["country"])
                else:
                    new_login = generate_random_email()
                print("Thông tin mới:", new_login)
                driver.refresh()
                reg_data = fill_registration_form(driver, wait, skip_cookies=True,
                                                  phone_override=new_login,
                                                  country_override=reg_data["country"])
                continue

        if success:
            with open("nvr_data.txt", "a", encoding="utf-8") as f:
                f.write(f"{reg_data['login']}|{reg_data['fb_pass']}\n")
            print("Đã lưu vào nvr_data.txt:", reg_data['login'], reg_data['fb_pass'])
        else:
            print("Không đạt confirm sau 100 lần thử.")
        driver.quit()
        print("Khởi động lại trình duyệt để tạo account mới...\n")
        time.sleep(3)

# ---------------------- Hỗ trợ chạy đa luồng ----------------------
def worker_thread():
    try:
        create_account_function1()
    except Exception as e:
        print("Lỗi trong thread:", e)

if __name__ == "__main__":
    print("Chức năng 1: Đăng ký tài khoản (phone hoặc email) đến màn hình confirm và lưu dữ liệu (headless, đa luồng).")
    num_threads = input("Nhập số lượng thread (số luồng): ").strip()
    try:
        num_threads = int(num_threads)
    except:
        num_threads = 1
    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=worker_thread)
        t.daemon = True
        t.start()
        threads.append(t)
    for t in threads:
        t.join()