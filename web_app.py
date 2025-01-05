
import streamlit as st
from streamlit.components.v1 import html
import time
import requests, json
import pandas as pd
import os

correct_password = "dt2025"

# 스타일 중앙 정렬
st.markdown("""
    <style>
    .block-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 150vh;
    }
    </style>
    """, unsafe_allow_html=True)

# 세션 상태를 사용하여 비밀번호 체크
if 'password_verified' not in st.session_state:
    st.session_state.password_verified = False
if 'password_attempted' not in st.session_state:
    st.session_state.password_attempted = False

def korean_to_ascii(text):
    # 한글을 임의의 알파벳으로 변환
    result = []
    for char in text:
        if '가' <= char <= '힣':  # 한글 음절 범위 확인
            # 유니코드 기반 간단 변환 (임의의 규칙 적용)
            result.append(chr((ord(char) - ord('가')) % 26 + ord('a')))
        else:
            # 한글이 아니면 그대로 추가
            result.append(char)
    return ''.join(result)

def core_map(address):
    import re
    import requests
    import json
    import folium
    from folium import GeoJson
    from folium import Choropleth
    from folium import Map
    from branca.element import Figure
    with open('outline.geojson', 'r', encoding='utf-8') as f:
        seoul_geo = json.load(f)
    plus_seoul = pd.read_csv('center_point.csv', encoding='utf-8')
    plus_seoul = plus_seoul[['읍면동명','X','Y']]
    plus_seoul['거리'] = ''
    plus_seoul['시간'] = ''

    def get_detail_number(response):
        data = response.json()
        rows = data.get('rows', [])
        elements = rows[0].get('elements', [])
        distance = elements[0].get('distance', {}).get('text')
        duration =  elements[0].get('duration', {}).get('text')
        return  [distance, duration]
    def DistanceFrom_Company(X,Y):
        API= "AIzaSyARXHvSHmYNIpjHMmWh2xhkLVsvPKxDKbg"
        #X=‘126.970418'
        #Y=‘37.584658'
        destX= st.session_state.lng
        destY= st.session_state.lat
        url = f"https://maps.googleapis.com/maps/api/distancematrix/json?units=metric&mode=transit&origins={Y},{X}&destinations={destY},{destX}&region=KR&key={API}"
        payload = {}
        headers = {}
        response = requests.request("GET", url,headers=headers, data=payload)
        result = get_detail_number(response)
        return result
    for i in range(len(plus_seoul)):
        X = float(plus_seoul.loc[i, 'X'])
        Y = float(plus_seoul.loc[i, 'Y'])
        try:
            dist,time = DistanceFrom_Company(X, Y)
        except:
            dist, time = '', ''
        plus_seoul.loc[i,'거리'] = dist
        plus_seoul.loc[i,'시간'] = time
    sector = pd.read_csv('center_point.csv', encoding='utf-8')
    plus_seoul['지역구'] = sector["시도명"] + " " + sector["시군구명"] + " " + sector["읍면동명"]
    # 거리 파싱 함수
    def parse_distance(distance_str):
        match = re.match(r"([\d\.]+)\s*km", distance_str)
        if match:
            return float(match.group(1))
        return None

    # 시간 파싱 함수
    def parse_duration(duration_str):
        hours = 0
        minutes = 0
        # 시간 추출
        hours_match = re.search(r"(\d+)\s*hour", duration_str)
        if hours_match:
            hours = int(hours_match.group(1))
        # 분 추출
        minutes_match = re.search(r"(\d+)\s*min", duration_str)
        if minutes_match:
            minutes = int(minutes_match.group(1))
        # 총 분으로 계산
        return hours * 60 + minutes

    plus_seoul["거리"] = plus_seoul["거리"].apply(parse_distance)
    plus_seoul["시간"] = plus_seoul["시간"].apply(parse_duration)

    sector = plus_seoul[['지역구','시간']]
    for i, value in enumerate(sector['지역구']):
        value = value.replace('제1', '1')
        value = value.replace('제2', '2')
        value = value.replace('제3', '3')
        value = value.replace('제4', '4')
        value = value.replace(',', '·')
        sector.loc[i, '지역구'] = value
    data = pd.DataFrame(sector.groupby('지역구')['시간'].median()).reset_index()
    sector = plus_seoul[['지역구','거리']]
    for i, value in enumerate(sector['지역구']):
        value = value.replace('제1', '1')
        value = value.replace('제2', '2')
        value = value.replace('제3', '3')
        value = value.replace('제4', '4')
        value = value.replace(',', '·')
        sector.loc[i, '지역구'] = value
    data = pd.merge(data, pd.DataFrame(sector.groupby('지역구')['거리'].median()).reset_index(), on = '지역구')
    Change_LIST = {'서울특별시 강서구 화곡제6동' : '서울특별시 강서구 화곡6동',
    '서울특별시 강서구 화곡제8동' :  '서울특별시 강서구 화곡8동',
    '서울특별시 구로구 구로제5동' :  '서울특별시 구로구 구로5동',
    '서울특별시 금천구 시흥제5동' :  '서울특별시 금천구 시흥5동',
    '서울특별시 노원구 상계3.4동' :  '서울특별시 노원구 상계3·4동',
    '서울특별시 노원구 상계6.7동' :  '서울특별시 노원구 상계6·7동',
    '서울특별시 노원구 중계2.3동' :  '서울특별시 노원구 중계2·3동',
    '서울특별시 도봉구 창제5동' :  '서울특별시 도봉구 창5동',
    '서울특별시 동작구 사당제5동' :  '서울특별시 동작구 사당5동',
    '서울특별시 성동구 금호2.3가동' :  '서울특별시 성동구 금호2·3가동',
    '서울특별시 영등포구 신길제5동' : '서울특별시 영등포구 신길5동',
    '서울특별시 영등포구 신길제6동' :  '서울특별시 영등포구 신길6동',
    '서울특별시 영등포구 신길제7동' :  '서울특별시 영등포구 신길7동',
    '서울특별시 종로구 종로1.2.3.4가동' : '서울특별시 종로구 종로1·2·3·4가동',
    '서울특별시 종로구 종로5.6가동' :  '서울특별시 종로구 종로5·6가동',
    '서울특별시 중구 신당제5동' :  '서울특별시 중구 신당5동',
    '서울특별시 중랑구 면목3.8동' :  '서울특별시 중랑구 면목3·8동',
    '서울특별시 중랑구 면목제5동' :  '서울특별시 중랑구 면목5동',
    '서울특별시 중랑구 면목제7동' :  '서울특별시 중랑구 면목7동'}
    for key, CHANGE in Change_LIST.items():
        for j, value in enumerate(data['지역구']):
            if value == key:
                data['지역구'].iloc[j] = CHANGE
                break
    for feature in seoul_geo['features']:
        region_name = feature['properties']['adm_nm']
        # DataFrame에서 해당 지역의 값을 찾아 properties에 추가
        feature['properties']['time'] = data.loc[data['지역구'] == region_name, '시간'].values[0]
        feature['properties']['Km'] = data.loc[data['지역구'] == region_name, '거리'].values[0]
    fig = Figure(width=500, height=400)  # 너비 500px, 높이 300px 설정
    bins = list(data.시간.quantile([0, 0.25, 0.5, 0.75, 1.0]))
    m = Map(
        location = [st.session_state.lat, st.session_state.lng],
        zoom_start = 11,
        tiles = 'cartodbpositron'
    )
    # Choropleth 추가
    Choropleth(
        geo_data=seoul_geo,
        name="choropleth",
        data=data,
        columns=["지역구", "시간"],  # 데이터프레임에서 사용할 열
        key_on="feature.properties.adm_nm",  # GeoJSON의 키와 데이터프레임 매칭
        fill_color="YlOrRd",  # 음영 색상 (Yellow to Green)
        fill_opacity=0.5,
        line_opacity=0.1,
        legend_name="대중교통 시간(버스/지하철)",
        bins=bins
    ).add_to(m)


    # Tooltip 추가
    GeoJson(
        data =seoul_geo,
        style_function=lambda x: {'fillColor': 'transparent', 'color': 'transparent'},
        tooltip=folium.GeoJsonTooltip(
            fields=['adm_nm', 'time', 'Km'],  # GeoJSON의 properties에서 표시할 필드
            aliases=['행정구 :', '대중 교통 (분) : ', '거리 (Km)  :'],  # 툴팁에 표시될 이름
            localize=True
        ),
    ).add_to(m)

    fig.add_child(m)
    m.save(f"map_{address}.html")

def create_map(address):
    if not st.session_state.password_verified and not st.session_state.password_attempted:
        with st.spinner("비밀번호 체크 중..."):
            with st.form(key='password_form'):
                password = st.text_input("비밀번호를 입력하세요:", type="password")
                submit_button = st.form_submit_button("확인")

        if submit_button:
            if password == correct_password:
                st.session_state.password_verified = True
                st.session_state.password_attempted = True
                st.success("비밀번호가 맞습니다! 함수를 실행합니다.")
                with st.spinner("계산 중(구글 검색)..."):
                    converted_address = korean_to_ascii(address)
                    file_path = f"map_{converted_address}.html"
                    if os.path.exists(file_path):
                        st.components.v1.html(open(file_path, "r").read(), height=400)
                    else:
                        core_map(converted_address)
                        st.components.v1.html(open(f"map_{converted_address}.html", "r").read(), height=400)
            else:
                st.session_state.password_verified = False
                st.session_state.password_attempted = True
                st.error("비밀번호가 틀렸습니다. 새로고침(F5) 해주세요.")
                time.sleep(3)
                st.stop()  # 이후 코드 실행을 멈춤


def get_location(address):
    params = {"query": f"{address}"}
    url = f"https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": "KakaoAK 30441c5ae09e2995e6644ce5bfacefc7"}
    api_json = json.loads(str(requests.get(url, headers=headers, params=params).text))
    location_details = [api_json['documents'][0]['address_name'], api_json['documents'][0]['place_url']]
    crd = {"lat": str(api_json['documents'][0]['y']), "lng": str(api_json['documents'][0]['x'])}
    st.session_state.location = location_details
    st.session_state.lat = crd['lat']
    st.session_state.lng = crd['lng']

# 상태 변수로 지도 생성 여부 추적
if 'map_generated' not in st.session_state:
    st.session_state.map_generated = False
    st.session_state.location = None
    st.session_state.lat = None
    st.session_state.lng = None


# 중앙 입력창
st.title("시간으로 그린 출퇴근 지도")
st.markdown("<h3 style='font-size: 16px;'>대중 교통 등급표 ver.서울</h3>", unsafe_allow_html=True)

address = st.text_input(label= '직장', placeholder="직장을 검색하세요 :", key="address", label_visibility="hidden")

if address and not st.session_state.password_verified and not st.session_state.password_attempted:
    with st.spinner("확인 중..."):
        get_location(address)
        st.write(f"주소 : {st.session_state.location[0]} 상세 : {st.session_state.location[1]}")
        time.sleep(2)
    st.session_state.map_generated = True

    
# 지도 생성 및 출력
if st.session_state.map_generated:
    folium_map = create_map(address)
