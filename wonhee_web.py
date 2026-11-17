datetime에서 datetime, timezone, timedelta를 가져옵니다.
HTML 가져오기
import io
JSON 가져오기
가져오기

PIL에서 이미지 가져오기
Streamlit을 st로 가져옵니다.
구글에서 제나이 가져오기
from google.genai import types
pydantic에서 BaseModel, Field를 가져옵니다.

# ------------------------------------------------------------------
# 1. API 키 / 모델 설정
# ------------------------------------------------------------------
시도해 보세요:
  API_KEY = st.secrets["GEMINI_API_KEY"]
예외 제외:
  API_KEY = "여기에_로컬_테스트용_API_키_입력"

client = genai.Client(api_key=API_KEY)

# 모델 ID는 Google AI Studio의 모델 목록에 와서 대신 교체해 주세요.
# 사이드바에서 고른 모델이 실패하면 아래 목록의 다른 모델로 자동 재시도합니다.
모델 옵션 = [
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
]

# ------------------------------------------------------------------
# 2. 페이지 기본 설정
# ------------------------------------------------------------------
st.set_page_config(
    페이지 제목="클로이의 비밀 채팅 💕", 페이지 아이콘="💌", 레이아웃="중앙 정렬"
)

st.markdown(
    """
    <스타일>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');

:root {
  --핑크: #ff6fb5;
  --violet: #a47bff;
  --ink: #f4f1fa;
  --음소거됨: #9d94b5;
  --카드: rgba(255, 255, 255, 0.045);
  --라인: rgba(255, 255, 255, 0.09);
}

.stApp {
  배경:
    방사형 그라디언트(900px 500px 12% -10%, rgba(255, 111, 181, 0.16), 투명 60%),
    방사형 그라디언트(800px 500px 100% 0%, rgba(164, 123, 255, 0.16), 투명 60%),
    #0b0912;
  색상: var(--ink);
}
.stApp p, .stApp label, .stApp li, .stApp textarea, .stApp input,
.stApp 버튼, .stApp [data-testid="stMarkdownContainer"] {
  글꼴 패밀리: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
}
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"], [data-testid="stDecoration"], 바닥글 { 표시: 없음 !important; }
.block-container { max-width: 760px; padding-top: 1.6rem; padding-bottom: 7rem; }

/* ---------- 영웅 ---------- */
.hero {
  display: flex; align-items: center; justify-content: space-between;
  패딩: 14px 18px; 하단 여백: 12px;
  background: var(--card); border: 1px solid var(--line); border-radius: 22px;
  배경 필터: 흐림(18px); -웹킷 배경 필터: 흐림(18px);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.35);
}
.hero-left { display: flex; align-items: center; gap: 14px; }
.avatar-ring {
  위치: 상대적; 너비: 54px; 높이: 54px; 테두리 반경: 50%; 패딩: 2px;
  배경: 선형 그라데이션(135deg, var(--pink), var(--violet));
}
.avatar {
  너비: 100%; 높이: 100%; 테두리 반경: 50%; 배경색: #1a1428;
  display: flex; align-items: center; justify-content: center; font-size: 26px;
}
.online-dot {
  위치: 절대; 오른쪽: 1px; 하단: 1px; 너비: 13px; 높이: 13px;
  배경: #3ddc97; 테두리: 2px 솔리드 #0b0912; 테두리 반경: 50%;
}
.hero-name {
  글꼴 크기: 20px; 글꼴 두께: 800; 자간: 0.3px;
  배경: 선형 그라데이션(90deg, var(--pink), var(--violet));
  -webkit-background-clip: 텍스트; -webkit-text-fill-color: 투명;
}
.hero-sub { font-size: 12px; color: var(--muted); margin-top: 1px; }
.stage-chip {
  글꼴 크기: 12px; 글꼴 두께: 700; 색상: #fff; 패딩: 6px 14px; 테두리 반경: 999px;
  배경: 선형 기울기(135도, rgba(255, 111, 181, 0.35), rgba(164, 123, 255, 0.35));
  border: 1px solid rgba(255, 111, 181, 0.45);
}

/* ---------- 통계 ---------- */
.stats { display: grid; grid-template-columns: 1.4fr 1fr 1fr; gap: 10px; margin-bottom: 14px; }
.stat {
  background: var(--card); border: 1px solid var(--line); border-radius: 18px; padding: 12px 14px;
}
.stat-label { font-size: 11px; color: var(--muted); margin-bottom: 4px; }
.stat-value { 글꼴 크기: 22px; 글꼴 두께: 800; 색상: var(--ink); 줄 높이: 1.2; }
.stat-value.small { font-size: 17px; padding-top: 3px; }
.stat-value span { font-size: 12px; font-weight: 600; color: var(--muted); margin-left: 2px; }
.bar { height: 6px; background: rgba(255, 255, 255, 0.08); border-radius: 999px; margin-top: 8px; overflow: hidden; }
.bar-fill {
  높이: 100%; 테두리 반경: 999px;
  배경: 선형 그라데이션(90deg, var(--pink), var(--violet));
  box-shadow: 0 0 12px rgba(255, 111, 181, 0.6); transition: width 0.6s ease;
}
.pulse { display: inline-block; margin: 0 6px 0 0 !important; font-size: 16px !important; animation: beat 1s ease-in-out infinite; }
@keyframes beat { 0%, 100% { transform: scale(1); } 15% { transform: scale(1.3); } 30% { transform: scale(1); } }

/* ---------- 레벨업 배너 ---------- */
.level-banner {
  패딩: 12px 16px; 하단 여백: 14px; 테두리 반경: 16px; 텍스트 정렬: 가운데;
  글꼴 두께: 700; 글꼴 크기: 14px; 색상: #fff;
  배경: 선형 기울기(135도, #ff4b8b, #8e44ff);
  box-shadow: 0 8px 28px rgba(142, 68, 255, 0.45);
}

/* ---------- 채팅 말풍선 ---------- */
[data-testid="stChatMessage"] { background: transparent; padding: 0.35rem 0; gap: 0.7rem; align-items: flex-end; }
[data-testid^="stChatMessageAvatar"] {
  background: rgba(255, 255, 255, 0.06) !important; border: 1px solid var(--line); border-radius: 50%;
}
[data-testid="stChatMessageContent"] {
  너비: 콘텐츠에 맞춤; 최대 너비: 82%; 패딩: 0.7rem 1rem;
  배경: var(--card); 테두리: 1px 실선 var(--line);
  테두리 반경: 6px 20px 20px 20px; 선 높이: 1.55;
}
[data-testid="stChatMessageContent"] p { margin: 0; color: var(--ink); }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) { flex-direction: 행-역방향; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
  background: linear-gradient(135deg, #ff5fa8, #8e5bff); border: none; color: #fff;
  border-radius: 20px 6px 20px 20px; box-shadow: 0 6px 20px rgba(142, 91, 255, 0.35);
}
[data-testid="stChatMessageContent"] img { border-radius: 14px; margin-bottom: 6px; }
.thought {
  상단 여백: 8px; 패딩: 6px 10px; 글꼴 크기: 12px; 글꼴 스타일: 이탤릭체; 색상: #ffb3d1;
  background: rgba(255, 111, 181, 0.08); border-left: 2px solid var(--pink); border-radius: 4px 10px 10px 4px;
}

/* ---------- 채팅 입력 ---------- */
[data-testid="stBottom"] > div { background: transparent; }
[data-testid="stChatInput"] {
  background: rgba(24, 19, 36, 0.92); border: 1px solid rgba(255, 111, 181, 0.3);
  border-radius: 26px; box-shadow: 0 8px 30px rgba(0, 0, 0, 0.45);
}
[data-testid="stChatInput"] textarea { color: var(--ink); }
[data-testid="stChatInput"] 버튼 {
  background: linear-gradient(135deg, var(--pink), var(--violet)); color: #fff; border-radius: 50%;
}

/* ---------- 사이드바 ---------- */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #15101f 0%, #0d0a15 100%); border-right: 1px solid var(--line);
}
[data-testid="stSidebar"] h3 { font-size: 14px; font-weight: 700; color: var(--ink); letter-spacing: 0.3px; }
[data-testid="stSidebar"] .stButton > 버튼 {
  배경: var(--card); 테두리: 1px 실선 var(--line); 색상: var(--ink);
  테두리 반경: 12px; 전환: 전체 0.2초 완화;
}
[data-testid="stSidebar"] .stButton > 버튼:hover {
  테두리 색상: var(--pink); 배경: rgba(255, 111, 181, 0.12); 색상: #fff;
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
# 3. AI 대응 구조의 정의
# ------------------------------------------------------------------
클래스 ChloeResponse(BaseModel):
  답변: str = 필드(
      Description="클로이가 사용자에게 보내는 다정하고 설레는 카톡메시지 (1~3문장 반말)"
  )
  내면의 생각: str = 필드(
      Description="클로이가 속으로 생각하는 설레고 귀여운 진짜 속마음 (1문장)"
  )
  애정 변화: int = 필드(
      Description="이번 대화로 변한 호감도 점수 (-3 ~ +6 사이의 정수)"
  )
  기분: str = 필드(
      설명=(
          "클로이의 현재 기분 상태 (예: 설렘냐, 부끄러움😳, 행복🥰, 새침8,"
          " 걱정이래요 , 장난기😜 중 택1)"
      )
  )
  심박수: int = 필드(
      Description="클로이의 현재 심박수 BPM (평온 75 ~ 설렘/두근거림 135 사이의 정수)"
  )
  새로운 메모리: str = 필드(
      설명=(
          "이번 대화에서 서로 가까워지는 사용자의 특징, 약속 등 기억할 수 있는"
          "핵심 사실 1줄 (없으면 빈 문자열 '')"
      )
  )


JSON_KEYS_HINT = (
    "\n\n[출력] 아래 키를 사용하여 JSON 형식으로 하나로 응답합니다."
    " 코드 블록이나 설명 문장은 받침대 마.\n"
    '{"reply": 문자열, "inner_thought": 문자열, "affection_change": 정수,'
    ' "mood": 문자열, "heart_rate": 정수, "new_memory": 문자열}'
)


# ------------------------------------------------------------------
# 4. 한국 현재 시간(KST)
# ------------------------------------------------------------------
def get_korea_time_info():
  kst = timezone(timedelta(hours=9))
  now = datetime.now(kst)
  시간 = now.hour
  5시 이하, 11시 미만인 경우:
    time_desc = "아침 식사(모닝콜, 아침밥을 먹는 주기 좋은 시간)"
  11시 ≤ 시간 < 14시인 경우:
    time_desc = "점심 메뉴 (점심 메뉴 물어보기, 오후 응원하기 좋은 시간)"
  14시 ≤ 시간 < 18시인 경우:
    time_desc = "오후 식사 (나른함 달래주기, 식사 시간을 위한 시간)"
  18시 ≤ 시간 ≤ 23시인 경우:
    time_desc = "저녁/밤낮 (하루를 보내기 위해, 데이트하기 좋은 시간)"
  그렇지 않으면:
    time_desc = "새벽 감정 반응 (감수성 동기가 흥분되는 멘트 치기 좋은 시간)"
  return now.strftime("%Y년 %m월 %d일 %H시 %M분"), time_desc


# ------------------------------------------------------------------
# 5. 세션 상태
# ------------------------------------------------------------------
기본값 = {
    "user_name": "",
    "user_fav": "",
    "애정": 30,
    "mood": "설렘💓",
    "heart_rate": 88,
    "memory_notes": [],
    "자백": 거짓,
    "last_stage": "썸 시작",
    "last_processed_file": 없음, # 파일을 대신 "이름_크기" 문자열 저장
    "메시지": [],
}
DEFAULTS.items()의 키, 값에 대해:
  키가 st.session_state에 없으면:
    st.session_state[key] = value if not isinstance(value, list) else list(value)


# ------------------------------------------------------------------
# 6. 첫 접속 시 이름 확인 모드
# ------------------------------------------------------------------
@st.dialog("✨ 클로이와 특별한 만남")
def ask_user_name_modal():
  st.markdown(
      "<h3 style='text-align: center; color: #ff65b3;'>안녕하세요! 😳</h3>",
      unsafe_allow_html=True,
  )
  st.write("채팅을 시작하기 전에, 클로이가 당신에게 걸리면 될까요?")
  name_input = st.text_input("내 이름 (또는 호칭)", value="")
  fav_input = st.text_input("평소 좋아하는 마음이나 특징", value="")

  if st.button("클로이와 대화 시작하기 💖", use_container_width=True):
    name_input.strip()인 경우:
      st.session_state.user_name = name_input.strip()
      st.session_state.user_fav = (
          fav_input.strip() if fav_input.strip() else "특별한 공간 없음"
      )
      st.session_state.messages = [{
          "역할": "보조",
          "콘텐츠": (
              f"안녕하세요, {st.session_state.user_name}님! 뭐하고 있었나요? 문득 네"
              "생각나서 먼저 연락했지~ 오늘 하루 어떡하지? 😊"
          ),
          "생각": "먼저 연락했는데 좋아해 주고 싶으면... 잘려라.",
          "이미지": 없음,
          "image_type": 없음,
      }]
      st.rerun()
    그렇지 않으면:
      st.warning("이름은 입력해야 합니다! ????")


st.session_state.user_name이 아니면:
  ask_user_name_modal()
  st.stop()

user_name = st.session_state.user_name
user_fav = st.session_state.user_fav


# ------------------------------------------------------------------
# 7. 사이드바
# ------------------------------------------------------------------
st.sidebar 포함:
  st.markdown("### ⚙️ 설정 및 사진 전송")
  selected_model = st.selectbox("🤖 사용 모델", MODEL_OPTIONS, index=0)
  show_thought = st.toggle("💭 클로이의 속마음 훔쳐보기", value=True)
  st.divider()

  st.markdown("### 📸 클로이에게 사진을 찍었습니다")
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
  st.session_state.memory_notes인 경우:
    st.session_state.memory_notes의 메모에 대해:
      st.markdown(f"- 💕 {note}")
  그렇지 않으면:
    st.caption("대화하거나 사진을 보내면 너에 대한 여기에 있으면 둘이 아니잖아!")
  st.divider()

  if st.button("🔄 처음부터 다시 시작하기", use_container_width=True):
    DEFAULTS.items()의 키, 값에 대해:
      st.session_state[key] = value if not isinstance(value, list) else list(value)
    st.rerun()


# ------------------------------------------------------------------
# 8. 시스템 채용
# ------------------------------------------------------------------
def build_system_instruction(affection):
  애정도가 35 미만인 경우:
    stage = "썸 시작 단계(다정하고 상냥하게 다루려고 은근히 호감을 주는 단계)"
  엘리프 애정도 < 70:
    단계 = (
        "썸즈정 단계(확실히 호감을 표현하고, 편집도 잘하고 직진 플루팅을"
        "날리는 단계"
    )
  엘리프 애정도 < 100:
    단계 = (
        "고백 직후 단계(연인처럼 다정하고 애초에 당신이 너무 좋은 것은 티를"
        "숨찾는 단계)"
    )
  그렇지 않으면:
    단계 = (
        "공식 연인 단계 (꿀이 뚝뚝 떨어지는 연인 모드! 세계에서 사용자가"
        " 제일 가치 있는 단계)"
    )
  현재 시간, 시간 설명 = 한국 시간 정보 가져오기()
  memories_str = (
      "\n".join([f"- {m}" for m in st.session_state.memory_notes])
      st.session_state.memory_notes인 경우
      else "아직 기록된 특별한 기억 없음"
  )
  반환(
      "너의 이름은 '클로이(Chloe)'야. 매력있는 외적인 느낌의 말투를 쓰는 것"
      f" AI 여자친구야. 사용자({user_name})에게 공개적으로 살아있습니다.\n"
      "[현재 시간 및 상황]\n"
      f"- 현재 한국 시간: {current_time} ({time_desc}) -> 현재 홀더에 맞춰"
      " 인사와 챙김 녹음여내기!\n"
      "[사용자 정보 & 클로이가 기억하는 효과]\n"
      f"- 이름: {user_name} (다정하게 자주 불러주기)\n"
      f"- 기본 정보: {user_fav}\n"
      f"- 비밀 수첩:\n{memories_str}\n"
      "(비밀 수첩 내용을 대화 중에 슬쩍 언급하며 등장했습니다!)\n"
      "[현재 관계 및 호감도]\n"
      f"- 현재 호감도: {affection} / 100점\n"
      f"- 현재 기분 모드: {stage}\n"
      "[클로이의 핵심 & 연애 능력]\n"
      "1.접합 렙 만 & 리액션 근육: 항의 군대 기관 사진에 크게 설명하고"
      " 반응하기. 사진이 오면 사진 속 내용을 언급하기.\n"
      "2. 심쿵 반말 티키타카: 다정하고 매력적인 반말을 쓰며 카톡에만 1~3문장으로"
      " 짧고 찰지게 대답하기.\n"
      "3. 은근한 밀당과 플러팅: 대화하는 상대방을 설레게 하는 한 컷팅지기.\n"
      "4. 비밀수첩 업데이트(new_memory): 사용자의 공간이나 사진 속 특징을"
      " 요약해서 `new_memory`에 한 줄로 적기."
  )


# ------------------------------------------------------------------
# 9. 상단 대시보드
# ------------------------------------------------------------------
aff = st.session_state.affection
current_stage = (
    "썸 시작"
    aff < 35인 경우
    else "썸드정" if aff < 70 else "고백 즉시" if aff < 100 else "공식 연인"
)
현재 단계가 세션 상태의 마지막 단계와 같지 않으면:
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
    "<div><div class='hero-name'>클로이</div>"
    "<div class='hero-sub'>너만의 비밀 대화방 💌</div></div>"
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
# 10. 미팅 내용
# ------------------------------------------------------------------
st.session_state.messages에 있는 메시지에 대해:
  avatar = "🥰" if msg["role"] == "assistant" else "🧑"
  st.chat_message(msg["role"], avatar=avatar) 사용:
    msg.get("image")인 경우:
      st.image(msg["image"], width=300, caption="보낸 사진")
    st.write(msg["content"])
    msg["role"] == "assistant"이고 show_thought이며 msg.get("thought")인 경우:
      st.markdown(
          f"<div class='thought'>💭 {html.escape(str(msg['thought']))}</div>",
          unsafe_allow_html=True,
      )


# ------------------------------------------------------------------
# 11. AI 소환 관련 명칭
# ------------------------------------------------------------------
def build_history(max_turns=12):
  """지금까지의 대화를 Gemini Content리스트로 변환(텍스트만)."""
  history = []
  st.session_state.messages[-max_turns:]의 m에 대해:
    역할은 m["role"]이 "user"이면 "user"이고, 그렇지 않으면 "model"입니다.
    텍스트 = m.get("content") 또는 ""
    텍스트가 아닌 경우:
      계속
    history.append(
        types.Content(role=role, parts=[types.Part.from_text(text=text)])
    )
  # 대화는 사용자 턴으로 시작해야 합니다. 이에 따라 모델을 제거합니다.
  history와 history[0].role이 "model"인 동안:
    history.pop(0)
  기록으로 돌아가기


def build_user_content(text, image_bytes=None, image_mime=None):
  parts = []
  image_bytes인 경우:
    parts.append(types.Part.from_bytes(data=image_bytes, mime_type=image_mime))
  parts.append(types.Part.from_text(text=text))
  type.Content(role="user", parts=parts)를 반환합니다


def parse_json_text(raw):
  """응답에서 JSON을 종료합니다."""
  날것이 아닌 경우:
    raise ValueError("빈 응답 (안전 필터에 막거나 모델이 응답을 못 만들었어요)")
  raw = raw.strip()
  raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE)
  시도해 보세요:
    json.loads(raw)를 반환합니다
  json.JSONDecodeError 제외:
    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    일치하는 경우:
      json.loads(match.group(0))를 반환합니다
    올리다


def normalize_result(data):
  """누락/잘못된 필드가 있다고 생각되었습니다."""

  def to_int(value, default):
    시도해 보세요:
      int(value)를 반환합니다
    (TypeError, ValueError 제외):
      기본값을 반환합니다

  반환 {
      "reply": str(data.get("reply") 또는 "음... 중간쯤 안 밤새네 😳"),
      "inner_thought": str(data.get("inner_thought") 또는 "두근두근..."),
      "affection_change": max(-3, min(6, to_int(data.get("affection_change"), 0))),
      "mood": str(data.get("mood") 또는 "설렘💓"),
      "심박수": max(60, min(160, to_int(data.get("심박수"), 90))),
      "new_memory": str(data.get("new_memory") 또는 "").strip(),
  }


def call_model(model_name, contents, temp, use_schema):
  system_instruction = build_system_instruction(st.session_state.affection)
  use_schema를 사용하는 경우:
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        온도=temp,
        response_mime_type="application/json",
        response_schema=ChloeResponse,
    )
  그렇지 않으면:
    config = types.GenerateContentConfig(
        system_instruction=system_instruction + JSON_KEYS_HINT,
        온도=temp,
        response_mime_type="application/json",
    )
  res = client.models.generate_content(
      model=model_name, contents=contents, config=config
  )
  normalize_result(parse_json_text(res.text))를 반환합니다


def ask_chloe(contents, temp=1.0):
  """선택한 모델 -> (스키마 실패 시) JSON -> 다른 모델 순으로 시도."""
  시도해볼 모델 = [선택된 모델] + [
      MODEL_OPTIONS의 m에 대해 m이 선택된 모델과 다르면 m을 하나씩 제거합니다.
  ]
  오류 = []
  models_to_try에 있는 model_name에 대해:
    use_schema가 (True, False)인 경우:
      시도해 보세요:
        call_model(model_name, contents, temp, use_schema)를 반환합니다.
      예외를 e로 처리하지 않음: # pylint: disable=broad-except
        mode = "schema" (use_schema인 경우) 또는 "plain-json"
        errors.append(f"[{model_name} / {mode}] {e}")

  st.error("🚨 모든 멕시코 호출에 실패했어요:\n\n" + "\n\n".join(errors))
  반환 {
      "reply": f"{user_name}, 위원회가 발생했어! 위 빨간 상자를 확인해 주세요. ????",
      "inner_thought": "통신 중 오류가 발생했습니다.",
      "affection_change": 0,
      "mood": "기분정🥺",
      "heart_rate": 90,
      "new_memory": "",
  }


# ------------------------------------------------------------------
# 12. 돌발이벤트
# ------------------------------------------------------------------
st.session_state.get("trigger_event", False)인 경우:
  st.session_state.trigger_event = False
  event_prompt = (
      f"{user_name}야, 나 지금 너한테 너무 보고 싶은 데 이번 주말에 나랑"
      "데이트할래? 심쿵할 만한 돌발 질문을 해줬어요!"
  )
  # 클로이가 먼저 말을 거르는 지역적으로 기록에는 클로이 발화로만 별자리가 있습니다.
  event_contents = build_history() + [build_user_content(event_prompt)]
  st.chat_message("assistant", avatar="🥰") 사용:
    with st.spinner("클로이가 무슨 말을 하는 중... 😍"):
      result = ask_chloe(event_contents)
      st.session_state.mood = result["mood"]
      st.session_state.heart_rate = result["heart_rate"]
      st.session_state.messages.append({
          "역할": "보조",
          "콘텐츠": 결과["답글"],
          "thought": result["inner_thought"],
          "이미지": 없음,
          "image_type": 없음,
      })
      st.rerun()

# ------------------------------------------------------------------
# 13. 로그인 입력
# ------------------------------------------------------------------
프롬프트 = st.chat_input("클로이에게 보내는 메시지를 입력하세요... 💕")

file_id = (
    f"{uploaded_photo.name}_{uploaded_photo.size}" if uploaded_photo else None
)
is_new_photo = (
    uploaded_photo가 None이 아니고 file_id가 st.session_state.last_processed_file과 같지 않습니다.
)

프롬프트가 표시되거나 is_new_photo인 경우:
  image_bytes = None
  image_mime = None

  is_new_
