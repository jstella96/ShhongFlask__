import json
import requests
from bs4 import BeautifulSoup

from flask import Flask,render_template,request,jsonify,session
from flask_restful import Api
from flask_cors import CORS
from places.matzip import Matzip
from places.janggwan import JangGwan
from jatooroute.jatoo import Jatoo

import os
import dialogflow
import uuid#세션아이디로 사용
from settings.config import DIALOG_CONFIG#프로젝트 아이디/API키가 설정된 모듈 import
from google.protobuf.json_format import MessageToJson   #costom playlode에 필요


#플라스크 앱 생성s
# Flask 객체 선언, 파라미터로 어플리케이션 패키지의 이름을 넣어줌.
app = Flask(__name__)
#JSON 응답 한글 처리
app.config['JSON_AS_ASCII']=False
#CORS에러 처리
# 데코레이터 이용, '/hello' 경로에 클래스 등록
CORS(app)
#플라스크 앱을 인자로 하여 Api객체 생성:클래스와 URI매핑
# Flask 객체에 Api 객체 등록
api = Api(app)

#별 추가 
app.config['JSON_AS_ASCII'] = False
#session을 위한 시크릿 키 설정:임의의 문자열- 세션에 값 설정시 반드시 필요
app.secret_key='dfgsdfg@$shfdsg&sfdsafh'

#GOOGLE_APPLICATION_CREDENTIALS키워드에 대한 설명:https://dialogflow.com/docs/reference/v2-auth-setup
#                                                ->https://cloud.google.com/docs/authentication/getting-started(2021.01.13기준)
#환경 변수 GOOGLE_APPLICATION_CREDENTIALS를 설정하여 애플리케이션 코드에 사용자 인증 정보를 제공
#API키를 환경변수로 등록
os.environ['GOOGLE_APPLICATION_CREDENTIALS']=DIALOG_CONFIG['GOOGLE_APPLICATION_CREDENTIALS']
#별 추가  끝 

#요청을 처리할 클래스와 요청 uri 매핑(라우팅)
#Api객체.add_resource(클래스명,'/요청url')
#/todos/<todo_id> url 패턴이면
#get방식이면 todo_id로 조회
#delete방식이면 todo_id로 삭제
#put방식이면 todo_id로 수정
#api.add_resource(Matzip,'/shoong/<lat>/<lng>')
api.add_resource(Matzip,'/places/matzip')
api.add_resource(JangGwan,'/places/janggwan')
api.add_resource(Jatoo,'/jatoo')
#/todos 로 요청시 get방식이면 전체조회
#                post방식이면 할일 등록
#api.add_resource(TodoList,'/todos')
#api.add_resource(Upload,'/upload')

if __name__ =='__main__':
    app.run(port=5000,host='0.0.0.0')



#별추가 :
@app.route('/message',methods=['GET'])
def handleMessage():#사용자 UI(Client App)에서 보낸 대화를 받는 함수
              #받은 대화는 다시 DialogFlow로 보낸다

    session['session_id'] = str(uuid.uuid4())#다른 어플리케이션의 UI사용시
    message= request.values.get('message')

    print('사용자 UI(Client App)에서 입력한 메시지:',message)

    #프로젝트 아이디 가져오기
    project_id = DIALOG_CONFIG.get('PROJECT_ID')
    #플라스크앱이  다얼로그 플로우로부터 받은 응답
    returnjson = response_from_dialogflow(project_id,session['session_id'],message,'ko')
    #다이얼로그로부터 받은 응답을 클라이언트 App(사용자 UI)에 전송
    return returnjson


def response_from_dialogflow(project_id, session_id, message, language_code):
    # step1. DialogFlow와 사용자가 상호작용할 세션 클라이언트 생성
    session_client = dialogflow.SessionsClient()
    session_path = session_client.session_path(project_id, session_id)
    # projects/프로젝트아이디/agent/sessions/세션아이디 로 생성된다
    print('[session_path]', session_path, sep='\n')
    if message:  # 사용자가 대화를 입력한 경우.대화는 utf-8로 인코딩된 자연어.256자를 넘어서는 안된다
        # step2.사용자 메시지(일반 텍스트)로 TextInput생성
        text_input = dialogflow.types.TextInput(text=message, language_code=language_code)
        print('[text_input]', text_input, sep='\n')

        # step 3. 생성된 TextInput객체로 QueryInput객체 생성(DialogFlow로 전송할 질의 생성)
        query_input = dialogflow.types.QueryInput(text=text_input)
        print('[query_input]', query_input, sep='\n')

        response = session_client.detect_intent(session=session_path, query_input=query_input)
        print('[response]', response, sep='\n')
        # 가공 _ code에 따라서 실행이 달라짐 1 : 단순응답 (변화 필요) 2: 날씨 응답(파이썬)  3: 자전거가게 (스프링에서 처리, 고객 주소 필요)
        res = MessageToJson(response)#응답받고
        res = json.loads(res)#json으로 변환하여 결과값을 빼낼 수 있는 상태로

        isCode = is_json_key_present(res) #code 값 존재여부 판단/
        print(isCode)
        if isCode :
            code = res['queryResult']['fulfillmentMessages'][0]['payload']['code']

            if code == "2":# 날씨
                location = res['queryResult']['fulfillmentMessages'][0]['payload']['location']
                time = res['queryResult']['fulfillmentMessages'][0]['payload']['time']
                print(location)
                weatherInfo =  get_weather_info(location,time,code)
                return weatherInfo

            elif code == "3":
                msg = res['queryResult']['fulfillmentMessages'][0]['payload']['msg']
                return jsonify({'code': code, 'msg': msg})

            elif code == "4":
                return jsonify({'code': code})

        else :
            return jsonify({'code': '1' ,'msg':response.query_result.fulfillment_text})



# 다이얼로그플로우 봇이 응답한 텍스트
def is_json_key_present(json):
        try:
            buf = json['queryResult']['fulfillmentMessages'][0]['payload']['code']
        except KeyError:
            return False

        return True

def get_weather_info(location,time,code):
    Finallocation = location + '날씨'
    LocationInfo = ""
    NowTemp = ""
    CheckDust = []
    url = 'https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=1&ie=utf8&query=' + Finallocation
    hdr = {'User-Agent': (
        'mozilla/5.0 (windows nt 10.0; win64; x64) applewebkit/537.36 (khtml, like gecko) chrome/78.0.3904.70 safari/537.36')}
    req = requests.get(url, headers=hdr)
    html = req.text
    soup = BeautifulSoup(html,'html.parser')

    #에러 체크
    ErrorCheck = soup.find('span', {'class' : 'btn_select'})
    if 'None' in str(ErrorCheck):
        print("지역 검색 오류!")

    else:
        # 지역 정보
        for i in soup.select('span[class=btn_select]'):
            LocationInfo = i.text

        # 현재 온도
        NowTemp = soup.find('span', {'class': 'todaytemp'}).text + soup.find('span', {'class' : 'tempmark'}).text[2:]
        # 날씨 캐스트
        WeatherCast = soup.find('p', {'class' : 'cast_txt'}).text
        # 자외선 지수
        TodayUV = soup.find('span', {'class' : 'indicator'}).text[4:-2] + " " + soup.find('span', {'class' : 'indicator'}).text[-2:]
        # 미세먼지, 초미세먼지, 오존 지수
        CheckDust1 = soup.find('div', {'class': 'sub_info'})
        CheckDust2 = CheckDust1.find('div', {'class': 'detail_box'})
        for i in CheckDust2.select('dd'):
            CheckDust.append(i.text)
        FineDust = CheckDust[0][:-2] + " " + CheckDust[0][-2:]
        UltraFineDust = CheckDust[1][:-2] + " " + CheckDust[1][-2:]
        Ozon = CheckDust[2][:-2] + " " + CheckDust[2][-2:]

        # 내일 오전, 오후 온도 및 상태 체크
        tomorrowArea = soup.find('div', {'class': 'tomorrow_area'})
        tomorrowCheck = tomorrowArea.find_all('div', {'class': 'main_info morning_box'})

        # 내일 오전온도
        tomorrowMoring1 = tomorrowCheck[0].find('span', {'class': 'todaytemp'}).text
        tomorrowMoring2 = tomorrowCheck[0].find('span', {'class' : 'tempmark'}).text[2:]
        tomorrowMoring = tomorrowMoring1 + tomorrowMoring2
        #내일 오전상태
        tomorrowMState1 = tomorrowCheck[0].find('div', {'class' : 'info_data'})
        tomorrowMState2 = tomorrowMState1.find('ul', {'class' : 'info_list'})
        tomorrowMState3 = tomorrowMState2.find('p', {'class' : 'cast_txt'}).text
        tomorrowMState4 = tomorrowMState2.find('div', {'class' : 'detail_box'})
        tomorrowMState5 = tomorrowMState4.find('span').text.strip()
        tomorrowMState = tomorrowMState3 + " " + tomorrowMState5
        # 내일 오후온도
        tomorrowAfter1 = tomorrowCheck[1].find('p', {'class' : 'info_temperature'})
        tomorrowAfter2 = tomorrowAfter1.find('span', {'class' : 'todaytemp'}).text
        tomorrowAfter3 = tomorrowAfter1.find('span', {'class' : 'tempmark'}).text[2:]
        tomorrowAfter = tomorrowAfter2 + tomorrowAfter3
       # 내일 오후상태
        tomorrowAState1 = tomorrowCheck[1].find('div', {'class' : 'info_data'})
        tomorrowAState2 = tomorrowAState1.find('ul', {'class' : 'info_list'})
        tomorrowAState3 = tomorrowAState2.find('p', {'class' : 'cast_txt'}).text
        tomorrowAState4 = tomorrowAState2.find('div', {'class' : 'detail_box'})
        tomorrowAState5 = tomorrowAState4.find('span').text.strip()
        tomorrowAState = tomorrowAState3 + " " + tomorrowAState5
        if time=='today':
            resultMsg="["+location+"]"+" 현재 날씨 정보는 아래와 같습니다."+"<br><br>"+"온도: " + NowTemp +" " + WeatherCast+"<br>"+"자외선 지수: " + TodayUV+"<br>"+"미세먼지 농도: " + FineDust+"<br>"+"초미세먼지 농도: " + UltraFineDust
        elif time=='tomorrow' :
            resultMsg= "["+location+"]"+" 내일 날씨 정보는 아래와 같습니다." + "<br><br>" +"오전"+"<br>" + "온도: " + tomorrowMoring + " "+ tomorrowMState + "<br>" + "오후"+"<br>"+"온도: " + tomorrowAfter+" " +tomorrowAState

        return jsonify({'code': code , 'location': location, 'msg':resultMsg})
