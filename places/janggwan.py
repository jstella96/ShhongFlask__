from flask_restful import Resource,reqparse
from flask import make_response
import os
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class JangGwan(Resource):
    def __init__(self):
        # Headless Browser를 위한 옵션 설정
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=1920x1080')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36')

        # 크롬드라이버(chromedriver.exe)가 위치한 경로(절대 경로)
        driverPath = '{}\chromedriver.exe'.format(os.path.dirname(os.path.realpath(__file__)))
        self.driver = webdriver.Chrome(driverPath, options=options)
        #self.driver = webdriver.Chrome(driverPath)
        # 생성자에서 파라미터 받기
        # step1. RequestParser객체 생성
        self.parser = reqparse.RequestParser()
        # step2. RequestParser객체에 add_argument('파라미터명')로 모든 파라미터명 추가
        self.parser.add_argument('lat')
        self.parser.add_argument('lng')

    def get(self):
        try:
            args = self.parser.parse_args()
            lat = args['lat']
            lng = args['lng']
            print('lat:', lat)
            print('lng:', lng)
            # 2. WebDriver객체의 get메소드로 특정 사이트를 브라우저에 로딩(자동으로 크롬브라우저 실행)
            self.driver.get('https://www.google.co.kr/maps/search/관광명소/@{},{},14z'.format(lat, lng))
            WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="pane"]/div/div[1]/div/div/div[4]/div[1]/div/div[2]')))
            gwanGwangs = []
            #관광명소 정보
            # 가게정보(version1)
            names = self.driver.find_elements_by_xpath(
                '//*[@id="pane"]/div/div[1]/div/div/div[4]/div[1]/div/div[2]/div[1]/div[1]/div[1]/div[2]/h3/span')
            urls = self.driver.find_elements_by_xpath(
                '//*[@id="pane"]/div/div[1]/div/div/div[4]/div[1]/div/div[2]/div[2]/div[1]')
            addrs = self.driver.find_elements_by_xpath(
                '//*[@id="pane"]/div/div[1]/div/div/div[4]/div[1]/div/div[2]/div[1]/div[2]/span[6]')
            openTimes = self.driver.find_elements_by_xpath(
                '//*[@id="pane"]/div/div[1]/div/div/div[4]/div[1]/div/div[2]/div[1]/div[5]/span[2]/span[1]')
            scores = self.driver.find_elements_by_xpath(
                '//*[@id="pane"]/div/div[1]/div/div/div[4]/div[1]/div/div[2]/div[1]/div[1]/div[1]/div[2]/span[3]/span[1]/span[1]/span')
            # 가게정보 데이터 출력
            results = list(zip(names, urls, addrs, openTimes, scores))
            for name, url, addr, openTime, score in results:
                gwanGwang = {'name': name.text,
                          'url': url.get_attribute('style').replace('background-image: url("', '').replace('");', ''),
                          'addr': addr.text,
                          'openTime': openTime.text,
                          'score': score.text}
                gwanGwangs.append(gwanGwang)
            print(gwanGwangs)
            return make_response({'places': gwanGwangs})

        except TimeoutException as e:
                print('해당 페이지에 태그 요소가 존재하지 않거나,해당 페이지가 시간 내에 열리지 않았어요:',e)