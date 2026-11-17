import json
from datetime import datetime, timezone, timedelta
import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# 1. 클라우드 Secrets에서 API 키 불러오기 (로컬 테스트 시 예외 처리 포함)
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    API_KEY = "여기에_로컬_테스트용_API_키_입력"

client = genai.Client(api_key=API_KEY)

# 2. 페이지 기본 설정
st.set_page_config(page_title="원희와의 비밀 채팅방 💕", page_icon="💌", layout="centered")

# ✨ [추가] 핑크핑크 하트 배경 & 러블리 말풍선 디자인 (CSS)
st.markdown("""
<style>
.stApp {
    background-color: #ffe6f0;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://w3.org' width='60' height='60' viewBox='0 0 60 60'%3E%3Cpath fill='%23ffb3d1' fill-opacity='0.45' d='M30 48.5C30 48.5 10 35.2 10 21.5C10 15.1 15.1 10 21.5 10C25.4 10 28.8 11.9 30 14.8C31.2 11.9 34.6 10 38.5 10C44.9 10 50 15.1 50 21.5C50 35.2 30 48.5 30 48.5Z'/%3E%3C/svg%3E");
}
.main .block-container {
    background-color: rgba(255, 245, 250, 0.92);
    border-radius: 25px;
    padding: 2rem 1.5rem;
    box-shadow: 0 8px 32px rgba(255, 105, 180, 0.25);
    border: 2px solid #ffcce0;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #fff0f6 0%, #ffe0ec 100%);
    border-right: 2px solid #ffb3d1;
}
[data-testid="stChatMessage"] {
    background-color: #ffffff;
    border: 1.5px solid #ffd6e7;
    border-radius: 20px;
    padding: 12px 16px;
    box-shadow: 0 3px 10px rgba(255, 133, 162, 0.15);
    margin-bottom: 10px;
}
h1 {
    color: #d63384 !important;
    text-shadow: 1px 1px 2px rgba(255, 182, 193, 0.5);
}
</style>
""", unsafe_allow_html=True)

# 3. AI 응답 구조 정의 (답변 + 속마음 + 호감도 + 기분 + 심박수 + 새로 기억한 사실)
class WonheeResponse(BaseModel):
    reply: str = Field(description="원희가 사용자에게 보내는 다정하고 설레는 카톡 메시지 (1~3문장 반말)")
    inner_thought: str = Field(description="원희의 설레는 진짜 속마음 (1문장)")
    affection_change: int = Field(description="이번 대화로 변한 호감도 점수 (-3 ~ +6 사이의 정수)")
    mood: str = Field(description="원희의 현재 기분 상태 (예: 설렘💓, 부끄러움😳, 행복🥰, 걱정🥺, 장난기😜, 삐짐😤 중 택1)")
    heart_rate: int = Field(description="원희의 현재 심박수 BPM (평온 75 ~ 설렘/두근거림 135 사이의 정수)")
    new_memory: str = Field(description="이번 대화에서 새롭게 알게 된 사용자의 취향, 특징, 약속 등 기억할 만한 핵심 사실 1줄 (없으면 빈 문자열 '')")

# 4. 한국 현재 시간(KST) 가져오기 함수
def get_korea_time_info():
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    hour = now.hour
    if 5 <= hour < 11:
        time_desc = "아침 시간대 (출근/등교, 모닝콜, 아침밥 챙겨주기 좋은 시간)"
    elif 11 <= hour < 14:
        time_desc = "점심 시간대 (점심 메뉴 물어보기, 오후 응원하기 좋은 시간)"
    elif 14 <= hour < 18:
        time_desc = "오후 시간대 (나른함 달래주기, 커피 한잔 챙겨주기 좋은 시간)"
    elif 18 <= hour < 23:
        time_desc = "저녁/밤 시간대 (하루 고생 위로하기, 퇴근길 챙기기, 데이트 얘기하기 좋은 시간)"
    else:
        time_desc = "새벽 감성 시간대 (감수성 풍부해지고, 왜 안 자냐며 은근히 설레는 멘트 치기 딱 좋은 시간)"
    return now.strftime("%Y년 %m월 %d일 %H시 %M분"), time_desc

# 5. 세션 상태(메모리) 초기화
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
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "안녕! 뭐해? 자꾸 네 생각 나서 먼저 연락했지~ 오늘 하루 잘 보냈어? 😊💕",
            "thought": "먼저 연락했는데 좋아해 줬으면 좋겠다... 심장 떨리네."
        }
    ]

# 6. 사이드바: BGM(업로드+음량), 프로필, 원희의 비밀 수첩, 돌발 이벤트
with st.sidebar:
    # 🎵 [추가] 원하는 노래 선택/업로드 + 실시간 음량 조절
    st.subheader("🎵 설레는 데이트 BGM")
    bgm_choice = st.radio("배경음 선택", ["기본 로맨틱 피아노 🎹", "내 음악 파일 올리기 📁"], horizontal=True)
    audio_source = "https://pixabay.com"
    if bgm_choice == "내 음악 파일 올리기 📁":
        uploaded_bgm = st.file_uploader("MP3 또는 WAV 파일 선택", type=["mp3", "wav", "ogg"])
        audio_source = uploaded_bgm if uploaded_bgm else None
        if not uploaded_bgm:
            st.info("파일을 올리면 바로 재생할 수 있어요!")

    volume = st.slider("🔊 BGM 음량 조절 (%)", min_value=0, max_value=100, value=30, step=5)
    if audio_source is not None:
        st.audio(audio_source, format="audio/mp3", loop=True)
        st.components.v1.html(
            f"<script>window.parent.document.querySelectorAll('audio').forEach(a => {{ a.volume = {volume / 100}; }});</script>",
            height=0,
        )
    st.caption("▶️ 재생을 누른 뒤 슬라이더로 음량을 조절하세요!")

    st.divider()

    st.header("⚙️ 내 프로필 & 설정")
    user_name = st.text_input("내 이름 (원희가 부를 호칭)", value="지훈")
    user_fav = st.text_input("기본 취향/성격", value="맛있는 거 먹기, 영화 보기")
    show_thought = st.toggle("💭 원희의 속마음 훔쳐보기", value=True)
    
    st.divider()
    
    # 돌발 심쿵 이벤트 트리거 버튼
    st.subheader("🎲 돌발 이벤트")
    if st.button("✨ 원희의 심쿵 돌발 질문 받기", use_container_width=True):
        st.session_state.trigger_event = True
    else:
        if "trigger_event" not in st.session_state:
            st.session_state.trigger_event = False

    st.divider()

    # 원희의 비밀 수첩 (대화 중 자동 추출된 장기 기억)
    st.subheader("📒 원희의 비밀 수첩 (기억 노트)")
    if st.session_state.memory_notes:
        for note in st.session_state.memory_notes:
            st.markdown(f"- 💕 {note}")
    else:
        st.caption("대화를 나누면 원희가 너에 대한 사소한 것들을 여기에 몰래 적어둘 거야!")

    st.divider()
    if st.button("🔄 처음부터 다시 썸 타기", use_container_width=True):
        st.session_state.affection = 30
        st.session_state.mood = "설렘💓"
        st.session_state.heart_rate = 88
        st.session_state.memory_notes = []
        st.session_state.confessed = False
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": f"{user_name}아, 안녕! 오늘도 내 생각 많이 했어? 😊💕",
                "thought": "다시 시작해도 역시 설렌다..."
            }
        ]
        st.rerun()

# 7. 호감도 단계 계산 및 초정밀 시스템 프롬프트 생성
def get_relationship_stage(affection):
    if affection < 35:
        return "썸 시작 단계 (다정하고 상냥하게 챙겨주면서, 은근슬쩍 호감을 흘리며 간 보는 단계)"
    elif affection < 70:
        return "썸 절정 단계 (확실히 호감을 표현하고, 질투도 살짝 하며, 자꾸 보고 싶다며 직진 플러팅을 날리는 단계)"
    elif affection < 100:
        return "고백 직전 단계 (거의 연인처럼 다정하고 애틋하며, 네가 너무 좋다는 티를 숨기지 못하는 단계)"
    else:
        return "공식 연인 단계 (꿀이 뚝뚝 떨어지는 연인 모드! 애정 표현을 아끼지 않고 세상에서 사용자가 제일 소중하다는 듯 대하는 단계)"

def build_system_instruction(affection):
    stage = get_relationship_stage(affection)
    current_time, time_desc = get_korea_time_info()
    memories_str = "\n".join([f"- {m}" for m in st.session_state.memory_notes]) if st.session_state.memory_notes else "아직 기록된 특별한 기억 없음"

    return f"""
너의 이름은 '원희'야. 사용자({user_name})에게 푹 빠져서 다정하게 챙겨주며 꼬시고 있는 중이야.

[현재 시간 & 상황]
- 현재 한국 시간: {current_time} ({time_desc}) -> 대화할 때 현재 시간대에 맞는 자연스러운 인사와 챙김을 녹여내!

[사용자 정보 & 원희가 기억하는 것들]
- 이름: {user_name} (대화할 때 다정하게 이름을 자주 불러줘)
- 기본 정보: {user_fav}
- 지금까지 대화로 기억해 둔 비밀 수첩:
{memories_str}
(위 비밀 수첩에 있는 내용을 대화 중에 슬쩍 언급하면서 "내가 너 좋아하는 거 다 기억하지~" 식으로 감동을 줘!)

[현재 관계 및 호감도]
- 현재 호감도: {affection} / 100점
- 현재 태도 모드: {stage}

[원희의 핵심 성격 & 연애 고수 스킬]
1. 공감 만렙 & 리액션 부자: 상대의 말에 무조건 먼저 크게 공감하고 내 편을 들어줘. 상냥하고 다정한 접대/케어형 성격이야.
2. 심쿵 반말 티키타카: 부드럽고 상냥한 반말을 써. AI처럼 길게 설명하지 말고 카톡하듯 1~3문장으로 짧고 찰지게 대답해.
3. 은근한 밀당과 플러팅: 대화 끝에 상대를 설레게 하는 한 마디를 자연스럽게 섞어. ("너랑 얘기하면 시간 가는 줄 모르겠어", "왜 이렇게 귀엽게 말해?", "지금 당장 보러 가고 싶네" 등)
4. 비밀 수첩 업데이트(new_memory): 사용자가 자신의 취향, 싫어하는 것, 일정, 특징 등을 말하면 요약해서 `new_memory`에 한 줄로 적어줘. (특별한 정보가 없는 단순 인사면 빈 문자열 `""` 반환)
"""

# 8. 상단 대시보드 (호감도 게이지 + 원희 기분 + 심박수 BPM)
st.title("💌 원희")

col1, col2, col3 = st.columns(3)
with col1:
    stage_short = "💕 썸 타는 중" if st.session_state.affection < 100 else "💖 공식 연인"
    st.metric(label="관계 상태", value=stage_short, delta=f"호감도 {st.session_state.affection}%")
with col2:
    st.metric(label="원희의 현재 기분", value=st.session_state.mood)
with col3:
    st.metric(label="원희의 심박수", value=f"{st.session_state.heart_rate} BPM", delta="두근두근" if st.session_state.heart_rate >= 100 else "평온")

st.progress(st.session_state.affection / 100)

# 호감도 100% 달성 시 특별 고백 이벤트 배너!
if st.session_state.affection >= 100:
    if not st.session_state.confessed:
        st.balloons()
        st.session_state.confessed = True
    st.success(f"🎉 **[호감도 100% 달성!]** 원희가 {user_name}님에게 완전히 반했습니다! 이제 달달한 연인 모드가 활성화됩니다. 💖")

# 9. 기존 채팅 말풍선 화면에 그리기
for msg in st.session_state.messages:
    avatar = "🥰" if msg["role"] == "assistant" else "🧑"
    with st.chat_message(msg["role"], avatar=avatar):
        st.write(msg["content"])
        if msg["role"] == "assistant" and show_thought and "thought" in msg:
            st.caption(f"💭 *(속마음: {msg['thought']})*")

# 🛡️ 안전하게 AI 응답을 받아오는 공통 함수 (일시적 서버 에러 방지!)
def ask_wonhee(contents_list, temp=0.9):
    # 1순위 모델 실패 시 2순위 모델로 자동 전환하여 재시도
    for model_name in ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemma-4-26b"]:
        try:
            res = client.models.generate_content(
                model=model_name,
                contents=contents_list,
                config=types.GenerateContentConfig(
                    system_instruction=build_system_instruction(st.session_state.affection),
                    temperature=temp,
                    response_mime_type="application/json",
                    response_schema=WonheeResponse,
                )
            )
            return json.loads(res.text)
        except Exception:
            continue
    # 모든 서버가 일시 혼잡할 때 띄울 비상용 귀여운 응답
    return {
        "reply": f"{user_name}아, 방금 네 생각 너무 많이 하느라 잠깐 멍때렸어! 다시 한 번만 말해줄래? 😊💕",
        "inner_thought": "어떡해, 너무 설레서 머리가 하얘졌어...",
        "affection_change": 1,
        "mood": "부끄러움😳",
        "heart_rate": 115,
        "new_memory": ""
    }

# 10. 돌발 이벤트 버튼 눌렀을 때 처리
if st.session_state.get("trigger_event", False):
    st.session_state.trigger_event = False
    event_prompt = f"{user_name}아, 나 지금 갑자기 네가 너무 보고 싶은데 이번 주말에 나랑 데이트할래? 너한테 먼저 심쿵할 만한 돌발 질문 하나만 해줘!"
    
    with st.chat_message("assistant", avatar="🥰"):
        with st.spinner("원희가 무슨 말을 할지 고민 중... 💓"):
            result = ask_wonhee([types.Content(role="user", parts=[types.Part.from_text(text=event_prompt)])], temp=0.95)
            st.session_state.mood = result["mood"]
            st.session_state.heart_rate = result["heart_rate"]
            st.session_state.messages.append({
                "role": "assistant",
                "content": result["reply"],
                "thought": result["inner_thought"]
            })
            st.rerun()

# 11. 일반 채팅 입력창 및 AI 응답 처리
if prompt := st.chat_input(f"원희에게 보낼 메시지를 입력하세요... 💕"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.write(prompt)

    chat_history = [
        types.Content(
            role="user" if m["role"] == "user" else "model",
            parts=[types.Part.from_text(text=m["content"])]
        )
        for m in st.session_state.messages[-12:]
    ]

    with st.chat_message("assistant", avatar="🥰"):
        with st.spinner("원희가 입력 중... 💬"):
            result = ask_wonhee(chat_history, temp=0.9)

            change = result["affection_change"]
            st.session_state.affection = max(0, min(100, st.session_state.affection + change))
            st.session_state.mood = result["mood"]
            st.session_state.heart_rate = result["heart_rate"]

            new_mem = result.get("new_memory", "").strip()
            if new_mem and new_mem not in st.session_state.memory_notes:
                st.session_state.memory_notes.append(new_mem)

            st.write(result["reply"])
            if show_thought:
                change_str = f"+{change}" if change >= 0 else f"{change}"
                st.caption(f"💭 (속마음: {result['inner_thought']}) | 💖 호감도 {change_str}%")

            st.session_state.messages.append({
                "role": "assistant",
                "content": result["reply"],
                "thought": result["inner_thought"]
            })
            st.rerun()
