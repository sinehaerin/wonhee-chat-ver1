from datetime import datetime, timezone, timedelta
import io
import json
from PIL import Image
import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# 1. 클라우드 Secrets에서 API 키 불러오기
try:
  API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
  API_KEY = "여기에_로컬_테스트용_API_키_입력"

client = genai.Client(api_key=API_KEY)

# 2. 페이지 기본 설정
st.set_page_config(
    page_title="Chloe's Secret Chat 💕", page_icon="💌", layout="centered"
)

# 🎨 [세련된 3D 디자인 적용] 커스텀 CSS
st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at top, #120c1f 0%, #06070b 100%);
        color: #f0f2f6;
    }
    /* 3D 입체 글래스 카드 스타일 */
    .glass-card {
        background: rgba(25, 20, 38, 0.7);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 105, 180, 0.25);
        padding: 16px;
        border-radius: 20px;
        box-shadow: 0 12px 35px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.15);
        text-align: center;
        margin-bottom: 10px;
    }
    /* 홀로그램 타이틀 */
    .main-title {
        font-size: 30px;
        font-weight: 900;
        background: -webkit-linear-gradient(45deg, #ff65b3, #b174ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2px;
        letter-spacing: 1px;
    }
    .sub-title {
        text-align: center;
        color: #9a8fb2;
        font-size: 13px;
        margin-bottom: 20px;
    }
    /* 호감도 단계 업그레이드 배너 */
    .level-banner {
        background: linear-gradient(135deg, #ff4b72 0%, #9c27b0 100%);
        padding: 12px;
        border-radius: 14px;
        text-align: center;
        font-weight: bold;
        color: white;
        margin-bottom: 15px;
        box-shadow: 0 6px 20px rgba(156, 39, 176, 0.5);
    }
    .stCaption {
        color: #ff9fb2 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# 3. AI 응답 구조 정의
class ChloeResponse(BaseModel):
  reply: str = Field(
      description=(
          "클로이가 사용자에게 보내는 다정하고 설레는 카톡 메시지 (1~3문장 반말)"
      )
  )
  inner_thought: str = Field(
      description=(
          "클로이가 속으로 생각하는 설레고 귀여운 진짜 속마음 (1문장)"
      )
  )
  affection_change: int = Field(
      description="이번 대화로 변한 호감도 점수 (-3 ~ +6 사이의 정수)"
  )
  mood: str = Field(
      description=(
          "클로이의 현재 기분 상태 (예:"
          " 설렘💓, 부끄러움😳, 행복🥰, 새침😎, 걱정🥺, 장난기😜 중 택1)"
      )
  )
  heart_rate: int = Field(
      description=(
          "클로이의 현재 심박수 BPM (평온 75 ~ 설렘/두근거림 135 사이의 정수)"
      )
  )
  new_memory: str = Field(
      description=(
          "이번 대화에서 새롭게 알게 된 사용자의 취향, 특징, 약속 등 기억할 만한"
          " 핵심 사실 1줄 (없으면 빈 문자열 '')"
      )
  )


# 4. 한국 현재 시간(KST) 가져오기 함수
def get_korea_time_info():
  kst = timezone(timedelta(hours=9))
  now = datetime.now(kst)
  hour = now.hour
  if 5 <= hour < 11:
    time_desc = "아침 시간대 (모닝콜, 아침밥 챙겨주기 좋은 시간)"
  elif 11 <= hour < 14:
    time_desc = "점심 시간대 (점심 메뉴 물어보기, 오후 응원하기 좋은 시간)"
  elif 14 <= hour < 18:
    time_desc = "오후 시간대 (나른함 달래주기, 커피 한잔 챙겨주기 좋은 시간)"
  elif 18 <= hour < 23:
    time_desc = "저녁/밤 시간대 (하루 고생 위로하기, 데이트 얘기하기 좋은 시간)"
  else:
    time_desc = "새벽 감성 시간대 (감수성 풍부해지고 설레는 멘트 치기 좋은 시간)"
  return now.strftime("%Y년 %m월 %d일 %H시 %M분"), time_desc


# 5. 세션 상태 초기화 (이름과 취향 기본값 공백 처리)
if "user_name" not in st.session_state:
  st.session_state.user_name = ""
if "user_fav" not in st.session_state:
  st.session_state.user_fav = ""
if "affection" not in st.session_state:
  st.session_state.affection = 30
if "mood" not in st.session_state:
  st.session_state.mood = "설렘💓"
if "heart_rate" not in st.session_state:
  st.session_state.heart_rate = 88
if "memory_notes" not in st.session_state:
  st.session_state.memory_notes = []
if "confessed" not in st.session_state:
  st.session_state.confessed = False
if "last_stage" not in st.session_state:
  st.session_state.last_stage = "썸 시작"
if "last_processed_file" not in st.session_state:
  st.session_state.last_processed_file = None
if "messages" not in st.session_state:
  st.session_state.messages = []


# 6. [첫 접속 시 이름 확인 모달] (공백 기본값 적용)
@st.dialog("✨ Chloe와의 특별한 만남")
def ask_user_name_modal():
  st.markdown(
      "<h3 style='text-align: center; color: #ff65b3;'>Hi there! 😳</h3>",
      unsafe_allow_html=True,
  )
  st.write("채팅을 시작하기 전에, 클로이가 너를 뭐라고 부르면 될까?")
  # 공백 상태로 입력창 제공
  name_input = st.text_input("내 이름 (또는 호칭)", value="")
  fav_input = st.text_input("평소 좋아하는 취향이나 특징", value="")

  if st.button("클로이와 대화 시작하기 💖", use_container_width=True):
    if name_input.strip():
      st.session_state.user_name = name_input.strip()
      st.session_state.user_fav = (
          fav_input.strip() if fav_input.strip() else "특별한 취향 없음"
      )
      st.session_state.messages = [{
          "role": "assistant",
          "content": (
              f"Hey, {st.session_state.user_name}! 뭐 하고 있었어? 문득 네"
              " 생각나서 먼저 연락했지~ 오늘 하루 어땠어? 😊"
          ),
          "thought": (
              "먼저 연락했는데 좋아해 줬으면 좋겠다... 떨려라."
          ),
          "image": None,
