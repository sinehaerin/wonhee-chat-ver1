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

# 🎨 3D 세련된 디자인 적용 CSS
st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at top, #120c1f 0%, #06070b 100%);
        color: #f0f2f6;
    }
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


# 5. 세션 상태 초기화
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


# 6. 첫 접속 시 이름 확인 모달
@st.dialog("✨ Chloe와의 특별한 만남")
def ask_user_name_modal():
  st.markdown(
      "<h3 style='text-align: center; color: #ff65b3;'>Hi there! 😳</h3>",
      unsafe_allow_html=True,
  )
  st.write("채팅을 시작하기 전에, 클로이가 너를 뭐라고 부르면 될까?")
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
          "image_type": None,
      }]
      st.rerun()
    else:
      st.warning("이름은 꼭 입력해 줘야 돼! 🥺")


if not st.session_state.user_name:
  ask_user_name_modal()
  st.stop()

user_name = st.session_state.user_name
user_fav = st.session_state.user_fav


# 7. 사이드바 설정
with st.sidebar:
  st.markdown("### ⚙️ 설정 & 사진 전송")
  show_thought = st.toggle("💭 클로이의 속마음 훔쳐보기", value=True)
  st.divider()

  st.markdown("### 📸 클로이에게 사진 보내기")
  uploaded_photo = st.file_uploader(
      "오늘 먹은 음식, 풍경 등을 공유해보세요!",
      type=["jpg", "jpeg", "png", "webp"],
      key="sidebar_photo_uploader",
  )
  st.divider()

  if st.button("🎲 클로이의 심쿵 돌발 질문", use_container_width=True):
    st.session_state.trigger_event = True
  st.divider()

  st.markdown("### 📒 클로이의 비밀 수첩")
  if st.session_state.memory_notes:
    for note in st.session_state.memory_notes:
      st.markdown(f"- 💕 {note}")
  else:
    st.caption("대화하거나 사진을 보내면 너에 대한 걸 여기에 적어둘 거야!")
  st.divider()

  if st.button("🔄 처음부터 다시 시작하기", use_container_width=True):
    st.session_state.user_name = ""
    st.session_state.user_fav = ""
    st.session_state.affection = 30
    st.session_state.mood = "설렘💓"
    st.session_state.heart_rate = 88
    st.session_state.memory_notes = []
    st.session_state.confessed = False
    st.session_state.last_stage = "썸 시작"
    st.session_state.last_processed_file = None
    st.session_state.messages = []
    st.rerun()


# 8. 시스템 프롬프트 생성 함수
def build_system_instruction(affection):
  if affection < 35:
    stage = "썸 시작 단계 (다정하고 상냥하게 챙겨주며 은근히 호감을 흘리는 단계)"
  elif affection < 70:
    stage = (
        "썸 절정 단계 (확실히 호감을 표현하고, 질투도 살짝 하며 직진 플러팅을"
        " 날리는 단계)"
    )
  elif affection < 100:
    stage = (
        "고백 직전 단계 (연인처럼 다정하고 애틋하며 네가 너무 좋다는 티를"
        " 숨기지 못하는 단계)"
    )
  else:
    stage = (
        "공식 연인 단계 (꿀이 뚝뚝 떨어지는 연인 모드! 세상에서 사용자가"
        " 제일 소중한 단계)"
    )
  current_time, time_desc = get_korea_time_info()
  memories_str = (
      "\n".join([f"- {m}" for m in st.session_state.memory_notes])
      if st.session_state.memory_notes
      else "아직 기록된 특별한 기억 없음"
  )
  return (
      "너의 이름은 '클로이(Chloe)'야. 매력적이고 세련된 외국 느낌의 말투를 쓰는"
      f" AI 여자친구야. 사용자({user_name})에게 푹 빠져있어.\n[현재 시간 &"
      f" 상황]\n- 현재 한국 시간: {current_time} ({time_desc}) -> 현재 시간대에"
      " 맞는 자연스러운 인사와 챙김 녹여내기!\n[사용자 정보 & 클로이가 기억하는"
      f" 것들]\n- 이름: {user_name} (다정하게 자주 불러주기)\n- 기본 정보:"
      f" {user_fav}\n- 비밀 수첩:\n{memories_str}\n(비밀 수첩 내용을 대화 중에"
      " 슬쩍 언급하며 감동 주기!)\n[현재 관계 및 호감도]\n- 현재 호감도:"
      f" {affection} / 100점\n- 현재 태도 모드:"
      f" {stage}\n[클로이의 핵심 성격 & 연애 스킬]\n1. 공감 만렙 & 리액션 부자:"
      " 상대의 말이나 보낸 사진에 크게 공감하고 반응하기.\n2. 심쿵 반말"
      " 티키타카: 다정하고 매력적인 반말을 쓰며 카톡하듯 1~3문장으로 짧고"
      " 찰지게 대답하기.\n3. 은근한 밀당과 플러팅: 대화 끝에 상대를 설레게 하는"
      " 한 마디 던지기.\n4. 비밀 수첩 업데이트(new_memory): 사용자의 취향이나"
      " 사진 속 특징을 요약해서 `new_memory`에 한 줄로 적기."
  )


# 9. 상단 대시보드 UI
st.markdown("<div class='main-title'>💌 Chloe's Secret Chat</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='sub-title'>너만을 위한 AI 여자친구와의 비밀 대화방</div>",
    unsafe_allow_html=True,
)

current_stage = (
    "썸 시작"
    if st.session_state.affection < 35
    else (
        "썸 절정"
        if st.session_state.affection < 70
        else "고백 직전" if st.session_state.affection < 100 else "공식 연인"
    )
)
if current_stage != st.session_state.last_stage:
  st.balloons()
  st.markdown(
      f"<div class='level-banner'>🎉 [호감도 단계 업그레이드!] 새로운 연애"
      f" 모드 '{current_stage}'(이)가 해금되었습니다! 💖</div>",
      unsafe_allow_html=True,
  )
  st.session_state.last_stage = current_stage

col1, col2, col3 = st.columns(3)
with col1:
  st.markdown(
      f"""
        <div class="glass-card">
            <div style="font-size: 11px; color: #9a8fb2;">관계 상태</div>
            <div style="font-size: 17px; font-weight: bold; color: #ff65b3;">{current_stage}</div>
            <div style="font-size: 10px; color: #ff9fb2;">호감도 {st.session_state.affection}%</div>
        </div>
        """,
      unsafe_allow_html=True,
  )
with col2:
  st.markdown(
      f"""
        <div class="glass-card">
            <div style="font-size: 11px; color: #9a8fb2;">클로이의 기분</div>
            <div style="font-size: 17px; font-weight: bold; color: #b174ff;">{st.session_state.mood}</div>
        </div>
        """,
      unsafe_allow_html=True,
  )
with col3:
  st.markdown(
      f"""
        <div class="glass-card">
            <div style="font-size: 11px; color: #9a8fb2;">심박수</div>
            <div style="font-size: 17px; font-weight: bold; color: #ff4b72;">{st.session_state.heart_rate} BPM</div>
        </div>
        """,
      unsafe_allow_html=True,
  )

st.progress(st.session_state.affection / 100)
st.divider()

# 10. 채팅 대화 내용 렌더링
for msg in st.session_state.messages:
  avatar = "🥰" if msg["role"] == "assistant" else "🧑"
  with st.chat_message(msg["role"], avatar=avatar):
    if msg.get("image"):
      st.image(msg["image"], width=300, caption="보낸 사진")
    try:
      st.write(msg["content"])
    except Exception:
      pass
    if msg["role"] == "assistant" and show_thought and "thought" in msg:
      st.caption(f"💭 *(속마음: {msg['thought']})*")


# AI 응답 함수
def ask_chloe(contents_list, temp=0.9):
  model_name = "gemini-2.5-flash"
  try:
    res = client.models.generate_content(
        model=model_name,
        contents=contents_list,
        config=types.GenerateContentConfig(
            system_instruction=build_system_instruction(
                st.session_state.affection
            ),
            temperature=temp,
            response_mime_type="application/json",
            response_schema=ChloeResponse,
        ),
    )
    return json.loads(res.text)
  except Exception as e:
    st.error(
        f"🚨 [디버그 에러 발생] 모델: {model_name} / 에러 내용: {str(e)}"
    )
    return {
        "reply": f"{user_name}, 에러가 발생했어! 위 빨간 박스를 확인해줘. 🥺",
        "inner_thought": "통신 중 에러가 발생했습니다.",
        "affection_change": 0,
        "mood": "걱정🥺",
        "heart_rate": 90,
        "new_memory": "",
    }


# 11. 돌발 이벤트 처리
if st.session_state.get("trigger_event", False):
  st.session_state.trigger_event = False
  event_prompt = (
      f"{user_name}야, 나 지금 갑자기 네가 너무 보고 싶은데 이번 주말에 나랑"
      " 데이트할래? 심쿵할 만한 돌발 질문 하나만 해줘!"
  )
  with st.chat_message("assistant", avatar="🥰"):
    with st.spinner("클로이가 무슨 말을 할지 고민 중... 💓"):
      result = ask_chloe([event_prompt], temp=0.95)
      st.session_state.mood = result["mood"]
      st.session_state.heart_rate = result["heart_rate"]
      st.session_state.messages.append({
          "role": "assistant",
          "content": result["reply"],
          "thought": result["inner_thought"],
          "image": None,
          "image_type": None,
      })
      st.rerun()

# 12. 채팅 입력창
prompt = st.chat_input("클로이에게 보낼 메시지를 입력하세요... 💕")

is_new_photo = (
    uploaded_photo is not None
    and uploaded_photo != st.session_state.last_processed_file
)

if prompt or is_new_photo:
  image_bytes = None
  image_mime = None

  if is_new_photo:
    try:
      raw_image = Image.open(uploaded_photo)
      raw_image.thumbnail((1024, 1024))
      buffered = io.BytesIO()
      img_format = raw_image.format if raw_image.format else "JPEG"
      if img_format not in ["JPEG", "PNG", "WEBP"]:
        img_format = "JPEG"
      raw_image.save(buffered, format=img_format)
      image_bytes = buffered.getvalue()
      image_mime = f"image/{img_format.lower()}"
    except Exception as e:
      print(f"Image Compression Error: {e}")
      image_bytes = uploaded_photo.getvalue()
      image_mime = uploaded_photo.type or "image/jpeg"

    st.session_state.last_processed_file = uploaded_photo

  text_prompt = prompt if prompt else "사진 보냈어! 이거 어때?"

  st.session_state.messages.append({
      "role": "user",
      "content": text_prompt,
      "image": image_bytes,
      "image_type": image_mime,
  })

  with st.chat_message("user", avatar="🧑"):
    if image_bytes:
      st.image(image_bytes, width=300)
    st.write(text_prompt)

  if image_bytes:
    contents_to_send = [
        types.Part.from_bytes(data=image_bytes, mime_type=image_mime),
        text_prompt,
    ]
  else:
    contents_to_send = text_prompt

  with st.chat_message("assistant", avatar="🥰"):
    with st.spinner(
        "클로이가 사진을 보고 답변을 고민 중... 💬"
        if image_bytes
        else "클로이가 입력 중... 💬"
    ):
      result = ask_chloe(contents_to_send, temp=0.9)

      change = result["affection_change"]
      st.session_state.affection = max(
          0, min(100, st.session_state.affection + change)
      )
      st.session_state.mood = result["mood"]
      st.session_state.heart_rate = result["heart_rate"]

      new_mem = result.get("new_memory", "").strip()
      if new_mem and new_mem not in st.session_state.memory_notes:
        st.session_state.memory_notes.append(new_mem)

      st.write(result["reply"])

      if show_thought:
        change_str = f"+{change}" if change >= 0 else f"{change}"
        st.caption(
            f"💭 (속마음: {result['inner_thought']}) | 💖 호감도"
            f" {change_str}%"
        )

      st.session_state.messages.append({
          "role": "assistant",
          "content": result["reply"],
          "thought": result["inner_thought"],
          "image": None,
          "image_type": None,
      })

      st.rerun()
