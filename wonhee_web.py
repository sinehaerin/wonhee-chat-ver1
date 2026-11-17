from datetime import datetime, timezone, timedelta
import html
import io
import json
import re

from PIL import Image
import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# ------------------------------------------------------------------
# 1. API 키 / 모델 설정
# ------------------------------------------------------------------
try:
  API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
  API_KEY = "여기에_로컬_테스트용_API_키_입력"

client = genai.Client(api_key=API_KEY)

# 모델 ID는 Google AI Studio의 모델 목록에 나온 정확한 문자열로 맞춰주세요.
# 사이드바에서 고른 모델이 실패하면 아래 목록의 다른 모델로 자동 재시도합니다.
MODEL_OPTIONS = [
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
]

# ------------------------------------------------------------------
# 2. 페이지 기본 설정
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Chloe's Secret Chat 💕", page_icon="💌", layout="centered"
)

st.markdown(
    """
    <style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');

:root {
  --pink: #ff6fb5;
  --violet: #a47bff;
  --ink: #f4f1fa;
  --muted: #9d94b5;
  --card: rgba(255, 255, 255, 0.045);
  --line: rgba(255, 255, 255, 0.09);
}

.stApp {
  background:
    radial-gradient(900px 500px at 12% -10%, rgba(255, 111, 181, 0.16), transparent 60%),
    radial-gradient(800px 500px at 100% 0%, rgba(164, 123, 255, 0.16), transparent 60%),
    #0b0912;
  color: var(--ink);
}
.stApp p, .stApp label, .stApp li, .stApp textarea, .stApp input,
.stApp button, .stApp [data-testid="stMarkdownContainer"] {
  font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
}
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"], [data-testid="stDecoration"], footer { display: none !important; }
.block-container { max-width: 760px; padding-top: 1.6rem; padding-bottom: 7rem; }

/* ---------- Hero ---------- */
.hero {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 18px; margin-bottom: 12px;
  background: var(--card); border: 1px solid var(--line); border-radius: 22px;
  backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.35);
}
.hero-left { display: flex; align-items: center; gap: 14px; }
.avatar-ring {
  position: relative; width: 54px; height: 54px; border-radius: 50%; padding: 2px;
  background: linear-gradient(135deg, var(--pink), var(--violet));
}
.avatar {
  width: 100%; height: 100%; border-radius: 50%; background: #1a1428;
  display: flex; align-items: center; justify-content: center; font-size: 26px;
}
.online-dot {
  position: absolute; right: 1px; bottom: 1px; width: 13px; height: 13px;
  background: #3ddc97; border: 2px solid #0b0912; border-radius: 50%;
}
.hero-name {
  font-size: 20px; font-weight: 800; letter-spacing: 0.3px;
  background: linear-gradient(90deg, var(--pink), var(--violet));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.hero-sub { font-size: 12px; color: var(--muted); margin-top: 1px; }
.stage-chip {
  font-size: 12px; font-weight: 700; color: #fff; padding: 6px 14px; border-radius: 999px;
  background: linear-gradient(135deg, rgba(255, 111, 181, 0.35), rgba(164, 123, 255, 0.35));
  border: 1px solid rgba(255, 111, 181, 0.45);
}

/* ---------- Stats ---------- */
.stats { display: grid; grid-template-columns: 1.4fr 1fr 1fr; gap: 10px; margin-bottom: 14px; }
.stat {
  background: var(--card); border: 1px solid var(--line); border-radius: 18px; padding: 12px 14px;
}
.stat-label { font-size: 11px; color: var(--muted); margin-bottom: 4px; }
.stat-value { font-size: 22px; font-weight: 800; color: var(--ink); line-height: 1.2; }
.stat-value.small { font-size: 17px; padding-top: 3px; }
.stat-value span { font-size: 12px; font-weight: 600; color: var(--muted); margin-left: 2px; }
.bar { height: 6px; background: rgba(255, 255, 255, 0.08); border-radius: 999px; margin-top: 8px; overflow: hidden; }
.bar-fill {
  height: 100%; border-radius: 999px;
  background: linear-gradient(90deg, var(--pink), var(--violet));
  box-shadow: 0 0 12px rgba(255, 111, 181, 0.6); transition: width 0.6s ease;
}
.pulse { display: inline-block; margin: 0 6px 0 0 !important; font-size: 16px !important; animation: beat 1s ease-in-out infinite; }
@keyframes beat { 0%, 100% { transform: scale(1); } 15% { transform: scale(1.3); } 30% { transform: scale(1); } }

/* ---------- Level up banner ---------- */
.level-banner {
  padding: 12px 16px; margin-bottom: 14px; border-radius: 16px; text-align: center;
  font-weight: 700; font-size: 14px; color: #fff;
  background: linear-gradient(135deg, #ff4b8b, #8e44ff);
  box-shadow: 0 8px 28px rgba(142, 68, 255, 0.45);
}

/* ---------- Chat bubbles ---------- */
[data-testid="stChatMessage"] { background: transparent; padding: 0.35rem 0; gap: 0.7rem; align-items: flex-end; }
[data-testid^="stChatMessageAvatar"] {
  background: rgba(255, 255, 255, 0.06) !important; border: 1px solid var(--line); border-radius: 50%;
}
[data-testid="stChatMessageContent"] {
  width: fit-content; max-width: 82%; padding: 0.7rem 1rem;
  background: var(--card); border: 1px solid var(--line);
  border-radius: 6px 20px 20px 20px; line-height: 1.55;
}
[data-testid="stChatMessageContent"] p { margin: 0; color: var(--ink); }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) { flex-direction: row-reverse; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
  background: linear-gradient(135deg, #ff5fa8, #8e5bff); border: none; color: #fff;
  border-radius: 20px 6px 20px 20px; box-shadow: 0 6px 20px rgba(142, 91, 255, 0.35);
}
[data-testid="stChatMessageContent"] img { border-radius: 14px; margin-bottom: 6px; }
.thought {
  margin-top: 8px; padding: 6px 10px; font-size: 12px; font-style: italic; color: #ffb3d1;
  background: rgba(255, 111, 181, 0.08); border-left: 2px solid var(--pink); border-radius: 4px 10px 10px 4px;
}

/* ---------- Chat input ---------- */
[data-testid="stBottom"] > div { background: transparent; }
[data-testid="stChatInput"] {
  background: rgba(24, 19, 36, 0.92); border: 1px solid rgba(255, 111, 181, 0.3);
  border-radius: 26px; box-shadow: 0 8px 30px rgba(0, 0, 0, 0.45);
}
[data-testid="stChatInput"] textarea { color: var(--ink); }
[data-testid="stChatInput"] button {
  background: linear-gradient(135deg, var(--pink), var(--violet)); color: #fff; border-radius: 50%;
}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #15101f 0%, #0d0a15 100%); border-right: 1px solid var(--line);
}
[data-testid="stSidebar"] h3 { font-size: 14px; font-weight: 700; color: var(--ink); letter-spacing: 0.3px; }
[data-testid="stSidebar"] .stButton > button {
  background: var(--card); border: 1px solid var(--line); color: var(--ink);
  border-radius: 12px; transition: all 0.2s ease;
}
[data-testid="stSidebar"] .stButton > button:hover {
  border-color: var(--pink); background: rgba(255, 111, 181, 0.12); color: #fff;
}
[data-testid="stFileUploaderDropzone"] {
  background: var(--card); border: 1px dashed rgba(255, 111, 181, 0.4); border-radius: 14px;
}
[data-testid="stSidebar"] hr { border-color: var(--line); }
.stCaption, [data-testid="stCaptionContainer"] { color: var(--muted) !important; }
</style>
""",
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------
# 3. AI 응답 구조 정의
# ------------------------------------------------------------------
class ChloeResponse(BaseModel):
  reply: str = Field(
      description="클로이가 사용자에게 보내는 다정하고 설레는 카톡 메시지 (1~3문장 반말)"
  )
  inner_thought: str = Field(
      description="클로이가 속으로 생각하는 설레고 귀여운 진짜 속마음 (1문장)"
  )
  affection_change: int = Field(
      description="이번 대화로 변한 호감도 점수 (-3 ~ +6 사이의 정수)"
  )
  mood: str = Field(
      description=(
          "클로이의 현재 기분 상태 (예: 설렘💓, 부끄러움😳, 행복🥰, 새침😎,"
          " 걱정🥺, 장난기😜 중 택1)"
      )
  )
  heart_rate: int = Field(
      description="클로이의 현재 심박수 BPM (평온 75 ~ 설렘/두근거림 135 사이의 정수)"
  )
  new_memory: str = Field(
      description=(
          "이번 대화에서 새롭게 알게 된 사용자의 취향, 특징, 약속 등 기억할 만한"
          " 핵심 사실 1줄 (없으면 빈 문자열 '')"
      )
  )


JSON_KEYS_HINT = (
    "\n\n[출력 형식] 반드시 아래 키를 가진 JSON 객체 하나로만 응답해."
    " 코드블록이나 설명 문장은 붙이지 마.\n"
    '{"reply": 문자열, "inner_thought": 문자열, "affection_change": 정수,'
    ' "mood": 문자열, "heart_rate": 정수, "new_memory": 문자열}'
)


# ------------------------------------------------------------------
# 4. 한국 현재 시간(KST)
# ------------------------------------------------------------------
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


# ------------------------------------------------------------------
# 5. 세션 상태 초기화
# ------------------------------------------------------------------
DEFAULTS = {
    "user_name": "",
    "user_fav": "",
    "affection": 30,
    "mood": "설렘💓",
    "heart_rate": 88,
    "memory_notes": [],
    "confessed": False,
    "last_stage": "썸 시작",
    "last_processed_file": None,  # 파일 객체 대신 "이름_크기" 문자열 저장
    "messages": [],
}
for key, value in DEFAULTS.items():
  if key not in st.session_state:
    st.session_state[key] = value if not isinstance(value, list) else list(value)


# ------------------------------------------------------------------
# 6. 첫 접속 시 이름 확인 모달
# ------------------------------------------------------------------
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
          "thought": "먼저 연락했는데 좋아해 줬으면 좋겠다... 떨려라.",
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


# ------------------------------------------------------------------
# 7. 사이드바
# ------------------------------------------------------------------
with st.sidebar:
  st.markdown("### ⚙️ 설정 & 사진 전송")
  selected_model = st.selectbox("🤖 사용할 모델", MODEL_OPTIONS, index=0)
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
    for key, value in DEFAULTS.items():
      st.session_state[key] = value if not isinstance(value, list) else list(value)
    st.rerun()


# ------------------------------------------------------------------
# 8. 시스템 프롬프트
# ------------------------------------------------------------------
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
      f" AI 여자친구야. 사용자({user_name})에게 푹 빠져있어.\n"
      "[현재 시간 & 상황]\n"
      f"- 현재 한국 시간: {current_time} ({time_desc}) -> 현재 시간대에 맞는"
      " 자연스러운 인사와 챙김 녹여내기!\n"
      "[사용자 정보 & 클로이가 기억하는 것들]\n"
      f"- 이름: {user_name} (다정하게 자주 불러주기)\n"
      f"- 기본 정보: {user_fav}\n"
      f"- 비밀 수첩:\n{memories_str}\n"
      "(비밀 수첩 내용을 대화 중에 슬쩍 언급하며 감동 주기!)\n"
      "[현재 관계 및 호감도]\n"
      f"- 현재 호감도: {affection} / 100점\n"
      f"- 현재 태도 모드: {stage}\n"
      "[클로이의 핵심 성격 & 연애 스킬]\n"
      "1. 공감 만렙 & 리액션 부자: 상대의 말이나 보낸 사진에 크게 공감하고"
      " 반응하기. 사진이 오면 사진 속 내용을 구체적으로 언급하기.\n"
      "2. 심쿵 반말 티키타카: 다정하고 매력적인 반말을 쓰며 카톡하듯 1~3문장으로"
      " 짧고 찰지게 대답하기.\n"
      "3. 은근한 밀당과 플러팅: 대화 끝에 상대를 설레게 하는 한 마디 던지기.\n"
      "4. 비밀 수첩 업데이트(new_memory): 사용자의 취향이나 사진 속 특징을"
      " 요약해서 `new_memory`에 한 줄로 적기."
  )


# ------------------------------------------------------------------
# 9. 상단 대시보드
# ------------------------------------------------------------------
aff = st.session_state.affection
current_stage = (
    "썸 시작"
    if aff < 35
    else "썸 절정" if aff < 70 else "고백 직전" if aff < 100 else "공식 연인"
)
if current_stage != st.session_state.last_stage:
  st.balloons()
  st.markdown(
      "<div class='level-banner'>🎉 호감도 단계 UP! 새로운 연애 모드"
      f" [{html.escape(current_stage)}] 해금 💖</div>",
      unsafe_allow_html=True,
  )
  st.session_state.last_stage = current_stage

hr = int(st.session_state.heart_rate)
beat_sec = max(0.4, min(1.5, 60 / max(hr, 40)))
mood_safe = html.escape(str(st.session_state.mood))

st.markdown(
    "<div class='hero'>"
    "<div class='hero-left'>"
    "<div class='avatar-ring'><div class='avatar'>🥰</div><span class='online-dot'></span></div>"
    "<div><div class='hero-name'>Chloe</div>"
    "<div class='hero-sub'>너만을 위한 비밀 대화방 💌</div></div>"
    "</div>"
    f"<div class='stage-chip'>{html.escape(current_stage)}</div>"
    "</div>"
    "<div class='stats'>"
    "<div class='stat'><div class='stat-label'>호감도</div>"
    f"<div class='stat-value'>{aff}<span>%</span></div>"
    f"<div class='bar'><div class='bar-fill' style='width:{aff}%'></div></div></div>"
    "<div class='stat'><div class='stat-label'>클로이의 기분</div>"
    f"<div class='stat-value small'>{mood_safe}</div></div>"
    "<div class='stat'><div class='stat-label'>심박수</div>"
    f"<div class='stat-value'><span class='pulse' style='animation-duration:{beat_sec:.2f}s'>💓</span>{hr}<span>BPM</span></div></div>"
    "</div>",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# 10. 채팅 내용 렌더링
# ------------------------------------------------------------------
for msg in st.session_state.messages:
  avatar = "🥰" if msg["role"] == "assistant" else "🧑"
  with st.chat_message(msg["role"], avatar=avatar):
    if msg.get("image"):
      st.image(msg["image"], width=300, caption="보낸 사진")
    st.write(msg["content"])
    if msg["role"] == "assistant" and show_thought and msg.get("thought"):
      st.markdown(
          f"<div class='thought'>💭 {html.escape(str(msg['thought']))}</div>",
          unsafe_allow_html=True,
      )


# ------------------------------------------------------------------
# 11. AI 호출 관련 함수
# ------------------------------------------------------------------
def build_history(max_turns=12):
  """지금까지의 대화를 Gemini Content 리스트로 변환 (텍스트만)."""
  history = []
  for m in st.session_state.messages[-max_turns:]:
    role = "user" if m["role"] == "user" else "model"
    text = m.get("content") or ""
    if not text:
      continue
    history.append(
        types.Content(role=role, parts=[types.Part.from_text(text=text)])
    )
  # 대화는 user 턴으로 시작해야 안전하므로 앞쪽 model 턴 제거
  while history and history[0].role == "model":
    history.pop(0)
  return history


def build_user_content(text, image_bytes=None, image_mime=None):
  parts = []
  if image_bytes:
    parts.append(types.Part.from_bytes(data=image_bytes, mime_type=image_mime))
  parts.append(types.Part.from_text(text=text))
  return types.Content(role="user", parts=parts)


def parse_json_text(raw):
  """응답 텍스트에서 JSON을 안전하게 꺼낸다."""
  if not raw:
    raise ValueError("빈 응답 (안전 필터에 막혔거나 모델이 응답을 못 만들었어요)")
  raw = raw.strip()
  raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE)
  try:
    return json.loads(raw)
  except json.JSONDecodeError:
    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if match:
      return json.loads(match.group(0))
    raise


def normalize_result(data):
  """누락/잘못된 필드를 기본값으로 보정."""

  def to_int(value, default):
    try:
      return int(value)
    except (TypeError, ValueError):
      return default

  return {
      "reply": str(data.get("reply") or "음... 잠깐 말이 안 나오네 😳"),
      "inner_thought": str(data.get("inner_thought") or "두근두근..."),
      "affection_change": max(-3, min(6, to_int(data.get("affection_change"), 0))),
      "mood": str(data.get("mood") or "설렘💓"),
      "heart_rate": max(60, min(160, to_int(data.get("heart_rate"), 90))),
      "new_memory": str(data.get("new_memory") or "").strip(),
  }


def call_model(model_name, contents, temp, use_schema):
  system_instruction = build_system_instruction(st.session_state.affection)
  if use_schema:
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=temp,
        response_mime_type="application/json",
        response_schema=ChloeResponse,
    )
  else:
    config = types.GenerateContentConfig(
        system_instruction=system_instruction + JSON_KEYS_HINT,
        temperature=temp,
        response_mime_type="application/json",
    )
  res = client.models.generate_content(
      model=model_name, contents=contents, config=config
  )
  return normalize_result(parse_json_text(res.text))


def ask_chloe(contents, temp=1.0):
  """선택한 모델 -> (스키마 실패 시) 프롬프트 JSON -> 다른 모델 순으로 재시도."""
  models_to_try = [selected_model] + [
      m for m in MODEL_OPTIONS if m != selected_model
  ]
  errors = []
  for model_name in models_to_try:
    for use_schema in (True, False):
      try:
        return call_model(model_name, contents, temp, use_schema)
      except Exception as e:  # pylint: disable=broad-except
        mode = "schema" if use_schema else "plain-json"
        errors.append(f"[{model_name} / {mode}] {e}")

  st.error("🚨 모든 모델 호출에 실패했어요:\n\n" + "\n\n".join(errors))
  return {
      "reply": f"{user_name}, 에러가 발생했어! 위 빨간 박스를 확인해줘. 🥺",
      "inner_thought": "통신 중 에러가 발생했습니다.",
      "affection_change": 0,
      "mood": "걱정🥺",
      "heart_rate": 90,
      "new_memory": "",
  }


# ------------------------------------------------------------------
# 12. 돌발 이벤트
# ------------------------------------------------------------------
if st.session_state.get("trigger_event", False):
  st.session_state.trigger_event = False
  event_prompt = (
      f"{user_name}야, 나 지금 갑자기 네가 너무 보고 싶은데 이번 주말에 나랑"
      " 데이트할래? 심쿵할 만한 돌발 질문 하나만 해줘!"
  )
  # 클로이가 먼저 말을 거는 상황이므로 기록에는 클로
