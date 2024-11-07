from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import pickle
import time

import requests
from datetime import datetime
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class LibrarySeatBooking:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.cookies = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0',
            'Accept': 'application/json, text/plain, */*',
            'Sec-Ch-Ua': '"Chromium";v="130", "Microsoft Edge";v="130", "Not?A_Brand";v="99"',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Lan': '1',
            'Token': '7e3c17040c164f2192a7312f9bf170e4',
            'Sec-Ch-Ua-Mobile': '?0',
            'Content-Type': 'application/json;charset=UTF-8',
            'Origin': 'https://libzw.ustb.edu.cn',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Connection': 'close'
        }

    def login(self):
        """执行登录操作并获取cookies"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # 无头模式，取消注释启用
        driver = webdriver.Chrome(options=options)

        try:
            print("开始登录过程...")
            driver.get('https://libzw.ustb.edu.cn/mobile.html#/login')
            wait = WebDriverWait(driver, 10)

            # 输入用户名
            username_input = wait.until(EC.presence_of_element_located((
                By.XPATH, '/html/body/div/div/div/div/div/div[2]/div/div/div[1]/div[2]/input'
            )))
            username_input.send_keys(self.username)

            # 输入密码
            password_input = wait.until(EC.presence_of_element_located((
                By.XPATH, '/html/body/div/div/div/div/div/div[2]/div/div/div[2]/div[2]/input'
            )))
            password_input.send_keys(self.password)

            # 点击登录
            login_button = wait.until(EC.element_to_be_clickable((
                By.XPATH, '/html/body/div/div/div/div/div/div[2]/div/button'
            )))
            login_button.click()

            # 等待登录完成
            time.sleep(3)

            # 获取cookies
            cookies = driver.get_cookies()
            self.cookies = {cookie['name']: cookie['value'] for cookie in cookies}

            print("登录成功！")
            return True

        except Exception as e:
            print(f"登录失败: {str(e)}")
            return False

        finally:
            driver.quit()

    def query_available_seats(self, room_id, date):
        """查询可用座位"""
        print("\n开始查询可用座位...")
        url = f'https://libzw.ustb.edu.cn/ic-web/reserve'
        params = {
            'roomIds': room_id,
            'resvDates': date,
            'sysKind': '8'
        }

        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                cookies=self.cookies,
                verify=False
            )
            response.raise_for_status()
            data = response.json()

            if data['code'] != 0:
                raise Exception(f"查询失败: {data['message']}")

            available_seats = []
            for seat in data['data']:
                if not seat.get('resvInfo', []):
                    available_seats.append({
                        'devId': seat['devId'],
                        'devName': seat['devName']
                    })

            print(f"找到 {len(available_seats)} 个可用座位")
            for seat in available_seats:
                print(f"座位号: {seat['devName']}, 设备ID: {seat['devId']}")

            return available_seats

        except Exception as e:
            print(f"查询座位失败: {str(e)}")
            return None

    def reserve_seat(self, dev_id, start_time):
        """预约指定座位"""
        print(f"\n开始预约座位...")
        current_date = datetime.now().strftime('%Y-%m-%d')

        request_data = {
            "testName": "",
            "appAccNo": 125773391,
            "memberKind": 1,
            "resvDev": [dev_id],
            "resvMember": [125773391],
            "resvProperty": 0,
            "sysKind": 8,
            "resvBeginTime": f"{current_date} {start_time}",
            "resvEndTime": f"{current_date} 22:00:00"
        }

        try:
            response = requests.post(
                'https://libzw.ustb.edu.cn/ic-web/reserve',
                headers=self.headers,
                cookies=self.cookies,
                json=request_data,
                verify=False
            )

            response_data = response.json()
            if response_data['code'] == 0:
                print("座位预约成功！")
                return True
            else:
                print(f"预约失败: {response_data['message']}")
                return False

        except Exception as e:
            print(f"预约过程出错: {str(e)}")
            return False


def load_preferred_seats():
    """加载偏好座位列表"""
    try:
        with open('preferred_seats.txt', 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("未找到preferred_seats.txt文件，请创建文件并输入想要预约的座位号（每行一个）")
        return []


def main():
    # 设置登录信息
    username = "U202241007"  # 替换为你的用户名
    password = "Lib_Ustb@22"  # 替换为你的密码

    # 创建预约系统实例
    booking_system = LibrarySeatBooking(username, password)

    # 执行登录
    if not booking_system.login():
        print("登录失败，程序退出")
        return

    # 加载偏好座位列表
    preferred_seats = load_preferred_seats()
    if not preferred_seats:
        return

    # 获取预约时间
    while True:
        start_time = input("请输入预约开始时间 (格式 HH:MM:00，例如 12:05:00): ")
        try:
            # 验证时间格式是否正确且分钟必须是5的倍数
            datetime.strptime(start_time, '%H:%M:00')
            minutes = int(start_time[3:5])  # 获取分钟部分
            if minutes % 5 == 0:  # 确保分钟是5的倍数
                break
            else:
                print("分钟必须是5的倍数，请重新输入。")
        except ValueError:
            print("时间格式不正确，请重新输入")

    # 查询可用座位
    room_id = '100545037'
    date = datetime.now().strftime('%Y%m%d')
    available_seats = booking_system.query_available_seats(room_id, date)

    if not available_seats:
        print("没有找到可用座位")
        return

    # 查找匹配的偏好座位
    seat_mapping = {seat['devName']: seat['devId'] for seat in available_seats}
    for preferred_seat in preferred_seats:
        if preferred_seat in seat_mapping:
            print(f"\n找到匹配的偏好座位: {preferred_seat}")
            # 预约座位
            if booking_system.reserve_seat(seat_mapping[preferred_seat], start_time):
                print(f"成功预约座位 {preferred_seat}!")
                break
            else:
                print(f"预约座位 {preferred_seat} 失败，尝试下一个偏好座位")
    else:
        print("没有找到可用的偏好座位")


if __name__ == "__main__":
    main()