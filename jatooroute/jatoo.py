from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import os.path
from flask_restful import Resource,reqparse
from flask import make_response
from seleniumrequests import Chrome
import xmltodict

class Jatoo(Resource):
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument("disable-gpu")
        options.add_argument("lang=ko_KR")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36")

        options.add_experimental_option("prefs", {
            "download.default_directory": os.path.dirname(os.path.realpath(__file__)) + '\\download',
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })
        driverPath = '{}\chromedriver.exe'.format(os.path.dirname(os.path.realpath(__file__)))
        self.browser = webdriver.Chrome(driverPath, options=options)
        # 요청 파라미터를 파싱하기 위한 객체 생성
        self.parser = reqparse.RequestParser()
        # step2. RequestParser객체에 add_argument('파라미터명')로 모든 파라미터명 추가
        self.parser.add_argument('region')


    def get(self):
        args = self.parser.parse_args()
        region = args['region']
        # prefs = {'download.default_directory' : '/download/'}
        # options.add_experimental_option('prefs', prefs)
        #자투넷 이동

        self.browser.get("http://jatoo.net/Forum/Account/Login?returnUrl=%2F")


        #로그인
        self.browser.find_element_by_id("UserName").send_keys("firenze5064@naver.com")
        self.browser.find_element_by_id("Password").send_keys("mp116306!")
        self.browser.find_element_by_id("Password").send_keys(Keys.ENTER)
        #루트 검색 이동
        self.browser.get("http://jatoo.net/Route/Search")

        WebDriverWait(self.browser, 5).until(EC.presence_of_element_located((By.ID, "region")))
        self.browser.execute_script('province="{}";'.format(region))
        routeList = WebDriverWait(self.browser,3).until(EC.presence_of_element_located((By.XPATH,"//*[@id='search']")))
        routeList.click()#찾기버튼 클릭

        if region=='so':
            sleep(1)
        WebDriverWait(self.browser,5).until(EC.presence_of_element_located((By.XPATH,'//*[@id="results"]/li/a')))
        atags=self.browser.find_elements_by_xpath('//*[@id="results"]/li/a/div[1]')
        print(len(atags))

        WebDriverWait(self.browser, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="results"]/li/a')))
        atags = self.browser.find_elements_by_xpath('//*[@id="results"]/li/a')
        print(len(atags))
        # 루트 리스트
        # soup = BeautifulSoup(browser.page_source,"lxml")
        # routes = soup.select("#results > li > a")
        # 루트 상세 다운로드
        infos = []
        routes = []
        for idx in range(1, len(atags) + 1):
            try:
                self.browser.find_element_by_xpath("//*[@id='results']/li[{}]/a".format(idx)).click()
            except Exception as e:
                self.browser.back()
                self.browser.find_element_by_xpath("//*[@id='results']/li[{}]/a".format(idx)).click()

            routeInfo = self.browser.find_element_by_xpath("/html/body/div[1]/div/div/div[2]/ul[2]/li[1]/ul/li[1]").text
            routeTitle = routeInfo[3:]
            print('변경전:', routeTitle)
            realRouteTitle = routeTitle.replace("~", "-").replace(" ", "-")
            # for ind in range(len(routeTitle)):
            #     if routeTitle[ind].isspace() or routeTitle in '~':
            #         realRouteTitle = routeTitle.replace("~", "-")
            #         realRouteTitle = realRouteTitle.replace(" ","-")
            #         break
            #     realRouteTitle = routeTitle
            print('변경 후:', realRouteTitle)
            name = self.browser.find_element_by_xpath(
                        '/html/body/div[1]/div/div/div[2]/ul[2]/li[1]/ul/li[4]/a').text
            dateBefore = self.browser.find_element_by_xpath('/html/body/div[1]/div/div/div[2]/ul[2]/li[1]/ul/li[4]').text
            st = dateBefore.find('년')
            st = st - 4
            date = dateBefore[st:]
            infos.append({'filename':realRouteTitle+'.gpx','title':routeTitle,'name':name,'date':date})
            routes.append(realRouteTitle+'.gpx')

            id=self.browser.current_url.split('/')[-1]
            #다운로드
            self.browser.execute_script('location.href="http://jatoo.net/Route/Download?id={}&format=gpx&option=15"'.format(id))


            #sleep(2)
            self.browser.back()
        sleep(2)

        total_routes=[]
        for gpx in routes:
            route = {
                "type": "Feature",
                "properties": {

                },
                "geometry": {
                    "type": "MultiLineString",

                }
            }
            for info in infos:
                if gpx==info['filename']:
                    lists = {'filename':info['filename'],'title':info['title'],'name':info['name'],'date':info['date']}
                    #lists.append(info['filename'])
                    #lists.append(info['title'])
                    #lists.append(info['name'])
                    #lists.append(info['date'])
                    route['properties'] = lists

            with open("./jatooroute/download/"+gpx, encoding='utf8') as xml_file:
                data_dict = xmltodict.parse(xml_file.read())
                dics = dict(dict(dict(dict(data_dict).get('gpx')).get('trk')).get('trkseg')).get('trkpt')

                lis = []
                for dic in dics:
                    # print(dict(dic))
                    lis.append([dic['@lat'], dic.get('@lon')])

                route['geometry']["coordinates"] = [lis]
                total_routes.append(route)

        return make_response({'routes': total_routes})



if __name__ =='__main__':
    import json
    import xmltodict

    # open the input xml file and read
    # data in form of python dictionary
    # using xmltodict module

    route={
    "type": "Feature",
    "properties": {
        "filename": "장동건_2021_01_26_04_51.json",
        "userId": "shoong1000@naver.com",
        "userName": "장동건",
        "startTime": "2021_01_26_04_51"
    },
    "geometry": {
        "type": "MultiLineString",

    }
}


    with open("./jatooroute/download/SBS-서울-부산.gpx",encoding='utf8') as xml_file:
        data_dict = xmltodict.parse(xml_file.read())


        # generate the object using json.dumps()
        # corresponding to json data


        dics=dict(dict(dict(dict(data_dict).get('gpx')).get('trk')).get('trkseg')).get('trkpt')

        lis=[]
        for dic in dics:
            #print(dict(dic))
            lis.append([dic['@lat'],dic.get('@lon')])

        route['geometry']["coordinates"]=[lis]
        print(route)

        #odic=list(dict(dict(dic.get('gpx').get('trk').get('trkseg'))).get('trkpt'))
        #print(dict(map(dict,odic)))

        #json_data = json.dumps(data_dict)
        #print(json_data)


'''
{
    "type": "Feature",
    "properties": {
        "filename": "장동건_2021_01_26_04_51.json",
        "userId": "shoong1000@naver.com",
        "userName": "장동건",
        "startTime": "2021_01_26_04_51"
    },
    "geometry": {
        "type": "MultiLineString",
        "coordinates": [
            [
                [
                    126.8790555,
                    37.4786485
                ],
                [
                    126.8790555,
                    37.4786485
                ],
                [
                    126.8790555,
                    37.4786485
                ],
                [
                    126.8790555,
                    37.4786485
                ],
                [
                    126.8790555,
                    37.4786485
                ]
            ]
        ]
    }
}

'''
