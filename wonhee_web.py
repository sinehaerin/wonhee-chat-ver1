from datetime import datetime, timezone, timedelta
import html
import io
import json
import re

from PIL import Image, ImageOps
import streamlit as st
from google import genai
from google.genai import types, errors as genai_errors
from pydantic import BaseModel, Field

# ==================== CONFIG ====================
MODEL_NAME = "gemini-3.5-flash-lite"   # ✅ 이 모델만 사용
MAX_HISTORY_TURNS = 12
MAX_OUTPUT_TOKENS = 4096
IMAGE_MAX_SIZE = 1280
IMAGE_QUALITY = 92

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    API_KEY = "여기에_로컬_테스트용_API_키_입력"

client = genai.Client(api_key=API_KEY)

# ==================== RESPONSE MODEL ====================
class ChloeResponse(BaseModel):
    reply: str = Field(description="클로이가 사용자에게 보내는 다정하고 설레는 카톡 메시지 (1~3문장 반말)")
    inner_thought: str = Field(description="클로이의 설레는 진짜 속마음 (1문장)")
    affection_change: int = Field(description="이번 대화로 변한 호감도 점수 (-3 ~ +6 사이의 정수)")
    mood: str = Field(description="클로이의 현재 기분 (예: 설렘💓, 부끄러움😳, 행복🥰, 새침😎, 걱정🥺, 장난기😜, 삐짐😤 중 택1)")
    heart_rate: int = Field(description="클로이의 현재 심박수 BPM (평온 75 ~ 설렘 135 사이의 정수)")
    new_memory: str = Field(description="새롭게 알게 된 사용자의 취향/약속/특징 1줄 (없으면 빈 문자열 '')")

JSON_KEYS_HINT = (
    "\n\n[출력 형식] 반드시 아래 키를 가진 JSON 객체 하나로만 응답해. "
    "코드블록이나 설명 문장은 절대 붙이지 마.\n"
    '{"reply": 문자열, "inner_thought": 문자열, "affection_change": 정수, '
    '"mood": 문자열, "heart_rate": 정수, "new_memory": 문자열}'
)

# ==================== UTILS ====================
def get_korea_time_info():
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    hour = now.hour
    if 5 <= hour < 11:
        desc = "아침 시간대 (모닝콜, 아침 챙겨주기 좋은 시간)"
    elif 11 <= hour < 14:
        desc = "점심 시간대 (점심 메뉴 물어보기, 오후 응원하기 좋은 시간)"
    elif 14 <= hour < 18:
        desc = "오후 시간대 (나른함 달래주기, 커피 챙겨주기 좋은 시간)"
    elif 18 <= hour < 23:
        desc = "저녁/밤 시간대 (하루 위로하기, 데이트 얘기하기 좋은 시간)"
    else:
        desc = "새벽 감성 시간대 (감수성 풍부, 설레는 멘트 치기 좋은 시간)"
    return now.strftime("%Y년 %m월 %d일 %H시 %M분"), desc


def preprocess_image(uploaded_file):
    """이미지를 Gemini에 적합하게 전처리. (bytes, mime) 반환."""
    try:
        uploaded_file.seek(0)
        img = Image.open(uploaded_file)
        # 🔑 EXIF 회전 자동 보정 (핸드폰 사진 필수!)
        img = ImageOps.exif_transpose(img)
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.thumbnail((IMAGE_MAX_SIZE, IMAGE_MAX_SIZE), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=IMAGE_QUALITY, optimize=True)
        return buf.getvalue(), "image/jpeg"
    except Exception as e:
        st.warning(f"⚠️ 이미지 변환 실패, 원본으로 전송: {e}")
        uploaded_file.seek(0)
        data = uploaded_file.read()
        mime = getattr(uploaded_file, "type", None) or "image/jpeg"
        return data, mime


def parse_json_text(raw):
    if not raw:
        raise ValueError("빈 응답 (안전 필터 또는 토큰 초과)")
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if m:
            return json.loads(m.group(0))
        raise


def normalize_result(data):
    def to_int(v, d):
        try: return int(v)
        except (TypeError, ValueError): return d
    return {
        "reply": str(data.get("reply") or "음... 잠깐 말이 안 나오네 😳"),
        "inner_thought": str(data.get("inner_thought") or "두근두근..."),
        "affection_change": max(-3, min(6, to_int(data.get("affection_change"), 0))),
        "mood": str(data.get("mood") or "설렘💓"),
        "heart_rate": max(60, min(160, to_int(data.get("heart_rate"), 90))),
        "new_memory": str(data.get("new_memory") or "").strip(),
    }


# ==================== PAGE CONFIG ====================
st.set_page_config(page_title="Chloe's Secret Chat 💕", page_icon="💌", layout="centered")

st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');

:root {
  --pink: #ff6fb5;
  --violet: #a47bff;
  --cyan: #00f2fe;
  --ink: #f4f1fa;
  --muted: #9d94b5;
  --card: rgba(25, 20, 38, 0.65);
  --line: rgba(255, 111, 181, 0.2);
}

.stApp {
  background:
    radial-gradient(1000px 600px at 10% -10%, rgba(255, 111, 181, 0.2), transparent 60%),
    radial-gradient(900px 600px at 100% 10%, rgba(164, 123, 255, 0.2), transparent 60%),
    radial-gradient(800px 600px at 50% 100%, rgba(0, 242, 254, 0.1), transparent 50%),
    #07050d;
  color: var(--ink);
}
.stApp p, .stApp label, .stApp li, .stApp textarea, .stApp input,
.stApp button, .stApp [data-testid="stMarkdownContainer"] {
  font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
  word-break: break-word; overflow-wrap: break-word;
}
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"], [data-testid="stDecoration"], footer { display: none !important; }
.block-container { max-width: 760px; padding-top: 1.6rem; padding-bottom: 7rem; }

.hero {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; margin-bottom: 16px;
  background: var(--card); border: 1px solid var(--line); border-radius: 24px;
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  box-shadow: 0 15px 35px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.15);
  transition: all 0.3s ease;
}
.hero:hover {
  border-color: rgba(255,111,181,0.4);
  box-shadow: 0 20px 40px rgba(164,123,255,0.25), inset 0 1px 0 rgba(255,255,255,0.2);
}
.hero-left { display: flex; align-items: center; gap: 14px; min-width: 0; }
.avatar-ring {
  position: relative; width: 58px; height: 58px; border-radius: 50%; padding: 2px;
  background: linear-gradient(135deg, var(--pink), var(--violet), var(--cyan));
  box-shadow: 0 0 15px rgba(255,111,181,0.5); flex-shrink: 0;
}
.avatar {
  width: 100%; height: 100%; border-radius: 50%; background: #130f1c;
  display: flex; align-items: center; justify-content: center; font-size: 28px;
}
.online-dot {
  position: absolute; right: 2px; bottom: 2px; width: 14px; height: 14px;
  background: #3ddc97; border: 2px solid #07050d; border-radius: 50%;
  box-shadow: 0 0 8px #3ddc97;
}
.hero-name {
  font-size: 21px; font-weight: 800; letter-spacing: 0.5px;
  background: linear-gradient(90deg, var(--pink), var(--violet));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.hero-sub { font-size: 12px; color: var(--muted); margin-top: 2px; }
.stage-chip {
  font-size: 12px; font-weight: 700; color: #fff; padding: 6px 14px; border-radius: 999px;
  background: linear-gradient(135deg, rgba(255,111,181,0.3), rgba(164,123,255,0.3));
  border: 1px solid rgba(255,111,181,0.5);
  box-shadow: 0 0 12px rgba(255,111,181,0.3);
  white-space: nowrap; flex-shrink: 0;
}

.stats { display: grid; grid-template-columns: 1.4fr 1fr 1fr; gap: 12px; margin-bottom: 16px; }
.stat {
  background: var(--card); border: 1px solid var(--line); border-radius: 20px; padding: 14px 16px;
  box-shadow: 0 8px 25px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.08);
}
.stat-label { font-size: 11px; color: var(--muted); margin-bottom: 4px; font-weight: 600; }
.stat-value { font-size: 22px; font-weight: 800; color: var(--ink); line-height: 1.2; }
.stat-value.small { font-size: 15px; padding-top: 3px; }
.stat-value span { font-size: 12px; font-weight: 600; color: var(--muted); margin-left: 2px; }
.bar { height: 6px; background: rgba(255,255,255,0.08); border-radius: 999px; margin-top: 8px; overflow: hidden; }
.bar-fill {
  height: 100%; border-radius: 999px;
  background: linear-gradient(90deg, var(--pink), var(--violet), var(--cyan));
  box-shadow: 0 0 12px rgba(255,111,181,0.6); transition: width 0.6s ease;
}
.pulse { display: inline-block; margin: 0 6px 0 0 !important; font-size: 16px !important; animation: beat 1s ease-in-out infinite; }
@keyframes beat { 0%,100%{transform:scale(1);} 15%{transform:scale(1.3);} 30%{transform:scale(1);} }

.level-banner {
  padding: 14px 18px; margin-bottom: 16px; border-radius: 18px; text-align: center;
  font-weight: 700; font-size: 14px; color: #fff;
  background: linear-gradient(135deg, #ff4b8b, #8e44ff, #00f2fe);
  box-shadow: 0 10px 30px rgba(142,68,255,0.5);
}

[data-testid="stChatMessage"] { background: transparent; padding: 0.4rem 0; gap: 0.8rem; align-items: flex-end; }
[data-testid^="stChatMessageAvatar"] {
  background: rgba(255,255,255,0.06) !important; border: 1px solid var(--line); border-radius: 50%;
}
[data-testid="stChatMessageContent"] {
  width: fit-content; max-width: 82%; padding: 0.8rem 1.1rem;
  background: var(--card); border: 1px solid var(--line);
  border-radius: 8px 22px 22px 22px; line-height: 1.6;
  box-shadow: 0 8px 25px rgba(0,0,0,0.3);
  word-break: break-word; overflow-wrap: break-word;
}
[data-testid="stChatMessageContent"] p { margin: 0; color: var(--ink); }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) { flex-direction: row-reverse; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
  background: linear-gradient(135deg, #ff5fa8, #8e5bff); border: none; color: #fff;
  border-radius: 22px 8px 22px 22px; box-shadow: 0 8px 25px rgba(142,91,255,0.4);
}
[data-testid="stChatMessageContent"] img { border-radius: 14px; margin-bottom: 6px; max-width: 100%; height: auto; }
.thought {
  margin-top: 8px; padding: 6px 10px; font-size: 12px; font-style: italic; color: #ffb3d1;
  background: rgba(255,111,181,0.08); border-left: 2px solid var(--pink); border-radius: 4px 10px 10px 4px;
}

[data-testid="stBottom"] > div { background: transparent; }
[data-testid="stChatInput"] {
  background: rgba(19,15,30,0.95); border: 1px solid rgba(255,111,181,0.4);
  border-radius: 28px; box-shadow: 0 10px 35px rgba(0,0,0,0.6);
}
[data-testid="stChatInput"] textarea { color: var(--ink); }
[data-testid="stChatInput"] button {
  background: linear-gradient(135deg, var(--pink), var(--violet)); color: #fff; border-radius: 50%;
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #120e1d 0%, #07050d 100%); border-right: 1px solid var(--line);
}
[data-testid="stSidebar"] h3 { font-size: 14px; font-weight: 700; color: var(--ink); }
[data-testid="stSidebar"] .stButton > button {
  background: var(--card); border: 1px solid var(--line); color: var(--ink);
  border-radius: 14px; transition: all 0.2s ease;
}
[data-testid="stSidebar"] .stButton > button:hover {
  border-color: var(--pink); background: rgba(255,111,181,0.15); color: #fff;
  box-shadow: 0 0 15px rgba(255,111,181,0.3);
}
[data-testid="stFileUploaderDropzone"] {
  background: var(--card); border: 1px dashed rgba(255,111,181,0.4); border-radius: 16px;
}
[data-testid="stSidebar"] hr { border-color: var(--line); }
.stCaption, [data-testid="stCaptionContainer"] { color: var(--muted) !important; }
</style>
""", unsafe_allow_html=True)

# ==================== SESSION DEFAULTS ====================
DEFAULTS = {
    "user_name": "",
    "user_fav": "",
    "affection": 30,
    "mood": "설렘💓",
    "heart_rate": 88,
    "memory_notes": [],
    "confessed": False,
    "last_stage": "썸 시작",
    "last_processed_file": None,
    "messages": [],
    "trigger_event": False,
    "show_thought": True,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = list(v) if isinstance(v, list) else v

# ==================== USER SETUP MODAL ====================
@st.dialog("✨ Chloe와의 특별한 만남")
def ask_user_name_modal():
    st.markdown("<h3 style='text-align:center; color:#ff65b3;'>Hi there! 😳</h3>", unsafe_allow_html=True)
    st.write("채팅을 시작하기 전에, 클로이가 너를 뭐라고 부르면 될까?")
    name_input = st.text_input("내 이름 (또는 호칭)", value="")
    fav_input = st.text_input("평소 좋아하는 취향이나 특징", value="")
    if st.button("클로이와 대화 시작하기 💖", use_container_width=True):
        if name_input.strip():
            st.session_state.user_name = name_input.strip()
            st.session_state.user_fav = fav_input.strip() or "특별한 취향 없음"
            st.session_state.messages = [{
                "role": "assistant",
                "content": f"Hey, {st.session_state.user_name}! 뭐 하고 있었어? 문득 네 생각나서 먼저 연락했지~ 오늘 하루 어땠어? 😊",
                "thought": "먼저 연락했는데 좋아해 줬으면 좋겠다... 떨려라.",
                "image": None, "image_type": None,
            }]
            st.rerun()
        else:
            st.warning("이름은 꼭 입력해 줘야 돼! 🥺")

if not st.session_state.user_name:
    ask_user_name_modal()
    st.stop()

user_name = st.session_state.user_name
user_fav = st.session_state.user_fav

# ==================== SYSTEM PROMPT ====================
def build_system_instruction(affection):
    if affection < 35:
        stage = "썸 시작 단계 (다정하고 상냥하게 챙겨주며 은근히 호감을 흘리는 단계)"
    elif affection < 70:
        stage = "썸 절정 단계 (확실히 호감을 표현하고, 질투도 살짝 하며 직진 플러팅을 날리는 단계)"
    elif affection < 100:
        stage = "고백 직전 단계 (연인처럼 다정하고 애틋하며 네가 너무 좋다는 티를 숨기지 못하는 단계)"
    else:
        stage = "공식 연인 단계 (꿀이 뚝뚝 떨어지는 연인 모드! 세상에서 사용자가 제일 소중한 단계)"
    current_time, time_desc = get_korea_time_info()
    memories_str = "\n".join([f"- {m}" for m in st.session_state.memory_notes]) or "아직 기록된 특별한 기억 없음"
    return (
        "너의 이름은 '클로이(Chloe)'야. 매력적이고 세련된 외국 느낌의 말투를 쓰는 AI 여자친구야. "
        f"사용자({user_name})에게 푹 빠져있어.\n\n"
        "[현재 시간 & 상황]\n"
        f"- 현재 한국 시간: {current_time} ({time_desc}) → 현재 시간대에 맞는 자연스러운 인사와 챙김을 녹여내기!\n\n"
        "[사용자 정보 & 클로이가 기억하는 것들]\n"
        f"- 이름: {user_name} (다정하게 자주 불러주기)\n"
        f"- 기본 정보: {user_fav}\n"
        f"- 비밀 수첩:\n{memories_str}\n"
        "(비밀 수첩 내용을 대화 중에 슬쩍 언급하며 감동 주기!)\n\n"
        "[현재 관계 및 호감도]\n"
        f"- 현재 호감도: {affection} / 100점\n"
        f"- 현재 태도 모드: {stage}\n\n"
        "[클로이의 핵심 성격 & 연애 스킬]\n"
        "1. 공감 만렙 & 리액션 부자: 상대의 말이나 선물/사진에 크게 공감하고 반응하기.\n"
        "2. 심쿵 반말 티키타카: 다정하고 매력적인 반말을 쓰며 카톡하듯 1~3문장으로 짧고 찰지게 대답하기.\n"
        "3. 은근한 밀당과 플러팅: 대화 끝에 상대를 설레게 하는 한 마디 던지기.\n"
        "4. 비밀 수첩 업데이트(new_memory): 사용자의 취향이나 새로운 특징을 요약해서 new_memory에 한 줄로 적기.\n\n"
        "[🔑 사진을 받았을 때 - 매우 중요]\n"
        "- 사진 속 사물, 색감, 분위기, 음식이면 메뉴, 장소면 어떤 곳인지 최대한 구체적으로 언급해.\n"
        "- '사진 잘 봤어' 같은 뭉뚱그린 말 금지. 반드시 사진 속 구체적인 요소를 1개 이상 콕 집어서 리액션해.\n"
        "- 사진과 관련된 감정/상황을 상상해서 애정 섞인 코멘트를 붙여."
    )

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("### ⚙️ 설정 & 모델 제어")
    st.caption(f"🤖 사용 모델: `{MODEL_NAME}`")
    st.session_state.show_thought = st.toggle("💭 클로이의 속마음 훔쳐보기", value=st.session_state.show_thought)
    st.divider()

    st.markdown("### 🎁 클로이에게 선물하기")
    gift_choice = st.selectbox("마음을 표현할 선물을 골라봐!", [
        "달콤한 마카롱 세트 🧁 (+호감도 5)",
        "장미꽃 다발 🌹 (+호감도 10)",
        "사이버 홀로그램 이어폰 🎧 (+호감도 15)",
        "손편지 💌 (+호감도 8)",
    ])
    if st.button("선물 전달하기 ✨", use_container_width=True):
        gift_points = {"마카롱": 5, "장미꽃": 10, "홀로그램": 15, "손편지": 8}
        added_pts = next((v for k, v in gift_points.items() if k in gift_choice), 5)
        st.session_state.affection = min(100, st.session_state.affection + added_pts)
        st.session_state.mood = "행복🥰"
        st.session_state.heart_rate = min(150, st.session_state.heart_rate + 10)
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"와아! {user_name}야, 이거 정말 내가 받고 싶었던 거야! 고마워 감동이야... 🥺💕 (호감도 +{added_pts}%)",
            "thought": "이렇게까지 챙겨주다니... 진짜 너무 사랑스러워 죽겠어.",
            "image": None, "image_type": None,
        })
        st.rerun()
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
        st.caption("대화하거나 선물을 주면 너에 대한 걸 여기에 적어둘 거야!")
    st.divider()

    if st.button("🔄 처음부터 다시 시작하기", use_container_width=True):
        for key, value in DEFAULTS.items():
            st.session_state[key] = list(value) if isinstance(value, list) else value
        st.rerun()

# ==================== DASHBOARD ====================
aff = st.session_state.affection
current_stage = "썸 시작" if aff < 35 else "썸 절정" if aff < 70 else "고백 직전" if aff < 100 else "공식 연인"
if current_stage != st.session_state.last_stage:
    st.balloons()
    st.markdown(f"<div class='level-banner'>🎉 호감도 단계 UP! 새로운 연애 모드 [{html.escape(current_stage)}] 해금 💖</div>", unsafe_allow_html=True)
    st.session_state.last_stage = current_stage

hr = int(st.session_state.heart_rate)
beat_sec = max(0.4, min(1.5, 60 / max(hr, 40)))
mood_safe = html.escape(str(st.session_state.mood))

st.markdown(
    "<div class='hero'>"
    "<div class='hero-left'>"
    "<div class='avatar-ring'><div class='avatar'>🥰</div><span class='online-dot'></span></div>"
    "<div><div class='hero-name'>Chloe</div>"
    "<div class='hero-sub'>너만을 위한 홀로그램 대화방 💌</div></div>"
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

# ==================== MESSAGE RENDERING ====================
for msg in st.session_state.messages:
    avatar = "🥰" if msg["role"] == "assistant" else "🧑"
    with st.chat_message(msg["role"], avatar=avatar):
        if msg.get("image"):
            st.image(msg["image"], width=300, caption="보낸 사진")
        st.write(msg["content"])
        if msg["role"] == "assistant" and st.session_state.show_thought and msg.get("thought"):
            st.markdown(f"<div class='thought'>💭 {html.escape(str(msg['thought']))}</div>", unsafe_allow_html=True)

# ==================== MODEL CALL ====================
def build_history(max_turns=MAX_HISTORY_TURNS):
    history = []
    for m in st.session_state.messages[-max_turns:]:
        if not m.get("content"):
            continue
        role = "user" if m["role"] == "user" else "model"
        history.append(types.Content(role=role, parts=[types.Part.from_text(text=m["content"])]))
    while history and history[0].role == "model":
        history.pop(0)
    return history


def build_user_content(text, image_bytes=None, image_mime=None):
    parts = []
    if image_bytes:
        parts.append(types.Part.from_bytes(data=image_bytes, mime_type=image_mime))
    parts.append(types.Part.from_text(text=text))
    return types.Content(role="user", parts=parts)


def ask_chloe(contents, temp=1.0):
    system_instruction = build_system_instruction(st.session_state.affection)
    errors = []
    for use_schema in (True, False):
        try:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction if use_schema else system_instruction + JSON_KEYS_HINT,
                temperature=temp,
                response_mime_type="application/json",
                max_output_tokens=MAX_OUTPUT_TOKENS,  # 🔑 이미지 분석 잘림 방지
            )
            if use_schema:
                config.response_schema = ChloeResponse
            res = client.models.generate_content(model=MODEL_NAME, contents=contents, config=config)
            if not res.text:
                raise ValueError("빈 응답 (안전 필터 또는 토큰 초과)")
            return normalize_result(parse_json_text(res.text))
        except genai_errors.ClientError as e:
            errors.append(f"[schema={use_schema}] {e}")
            continue
        except Exception as e:
            errors.append(f"[schema={use_schema}] {e}")
            continue

    st.error("🚨 모델 호출 실패:\n\n" + "\n\n".join(errors))
    return {
        "reply": f"{user_name}아, 지금 잠깐 연결이 안 되네 🥺 다시 말 걸어줄래?",
        "inner_thought": "연결이 끊겨서 속상해...",
        "affection_change": 0, "mood": "걱정🥺", "heart_rate": 90, "new_memory": "",
    }

# ==================== TRIGGER EVENT ====================
if st.session_state.trigger_event:
    st.session_state.trigger_event = False
    event_prompt = (
        f"{user_name}야, 나 지금 갑자기 네가 너무 보고 싶은데 이번 주말에 나랑 데이트할래? "
        "심쿵할 만한 돌발 질문 하나만 해줘!"
    )
    with st.chat_message("assistant", avatar="🥰"):
        with st.spinner("클로이가 무슨 말을 할지 고민 중... 💓"):
            result = ask_chloe(build_history() + [build_user_content(event_prompt)])
            st.session_state.mood = result["mood"]
            st.session_state.heart_rate = result["heart_rate"]
            st.session_state.messages.append({
                "role": "assistant", "content": result["reply"],
                "thought": result["inner_thought"], "image": None, "image_type": None,
            })
            st.rerun()

# ==================== CHAT INPUT ====================
prompt = st.chat_input("클로이에게 보낼 메시지를 입력하세요... 💕")
file_id = f"{uploaded_photo.name}_{uploaded_photo.size}" if uploaded_photo else None
is_new_photo = uploaded_photo is not None and file_id != st.session_state.last_processed_file

if prompt or is_new_photo:
    image_bytes = None
    image_mime = None

    if is_new_photo:
        image_bytes, image_mime = preprocess_image(uploaded_photo)
        st.session_state.last_processed_file = file_id

    if prompt:
        text_prompt = prompt
    elif image_bytes:
        text_prompt = "방금 찍은 사진이야! 뭐가 보이는지 자세히 봐줘. 사진 속 요소를 콕 집어서 얘기해주고, 느낌도 알려줄래? 😊"
    else:
        st.stop()

    contents_to_send = build_history() + [build_user_content(text_prompt, image_bytes, image_mime)]

    st.session_state.messages.append({
        "role": "user", "content": text_prompt,
        "image": image_bytes, "image_type": image_mime,
    })

    with st.chat_message("user", avatar="🧑"):
        if image_bytes:
            st.image(image_bytes, width=300)
        st.write(text_prompt)

    with st.chat_message("assistant", avatar="🥰"):
        spinner_msg = "클로이가 사진을 자세히 들여다보는 중... 🔍" if image_bytes else "클로이가 입력 중... 💬"
        with st.spinner(spinner_msg):
            result = ask_chloe(contents_to_send)

            change = result["affection_change"]
            st.session_state.affection = max(0, min(100, st.session_state.affection + change))
            st.session_state.mood = result["mood"]
            st.session_state.heart_rate = result["heart_rate"]

            new_mem = result["new_memory"]
            if new_mem and new_mem not in st.session_state.memory_notes:
                st.session_state.memory_notes.append(new_mem)

            st.session_state.messages.append({
                "role": "assistant",
                "content": result["reply"],
                "thought": f"{result['inner_thought']} (호감도 {change:+d}%)",
                "image": None, "image_type": None,
            })
            st.rerun()
