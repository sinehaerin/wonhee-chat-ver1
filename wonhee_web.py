from datetime import datetime, timezone, timedelta
import json
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
st.set_page_config(
    page_title="원희와의 비밀 채팅방 💕", page_icon="💌", layout="centered"
)


# 3. AI 응답 구조 정의 (답변 + 속마음 + 호감도 + 기분 + 심박수 + 새로 기억한 사실)
class WonheeResponse(BaseModel):
  reply: str = Field(
      description=(
          "원희가 사용자에게 보내는 다정하고 설레는 카톡 메시지 (1~3문장 반말)"
      )
  )
  inner_thought: str = Field(
      description=(
          "원희가 속으로 생각하는 설레고 귀여운 진짜 속마음 (1문장)"
      )
  )
  affection_change: int = Field(
      description="이번 대화로 변한 호감도 점수 (-3 ~ +6 사이의 정수)"
  )
  mood: str = Field(
      description=(
          "원희의 현재 기분 상태 (예:"
          " 설렘💓, 부끄러움😳, 행복🥰, 걱정🥺, 장난기😜, 삐짐😤 중 택1)"
      )
  )
  heart_rate: int = Field(
      description=(
          "원희의 현재 심박수 BPM (평온 75 ~ 설렘/두근거림 135 사이의 정수)"
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
    time_desc = "아침 시간대 (출근/등교, 모닝콜, 아침밥 챙겨주기 좋은 시간)"
  elif 11 <= hour < 14:
    time_desc = "점심 시간대 (점심 메뉴 물어보기, 오후 응원하기 좋은 시간)"
  elif 14 <= hour < 18:
    time_desc = "오후 시간대 (나른함 달래주기, 커피 한잔 챙겨주기 좋은 시간)"
  elif 18 <= hour < 23:
    time_desc = (
        "저녁/밤 시간대 (하루 고생 위로하기, 퇴근길 챙기기, 데이트 얘기하기"
        " 좋은 시간)"
    )
  else:
    time_desc = (
        "새벽 감성 시간대 (감수성 풍부해지고, 왜 안 자냐며 은근히 설레는 멘트"
        " 치기 딱 좋은 시간)"
    )
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
if "last_processed_file" not in st.session_state:
  st.session_state.last_processed_file = None  # 중복 업로드 방지용 키
if "messages" not in st.session_state:
  st.session_state.messages = [{
      "role": "assistant",
      "content": "안녕! 뭐해? 자꾸 네 생각 나서 먼저 연락했지~ 오늘 하루 잘 보냈어? 😊",
      "thought": "먼저 연락했는데 좋아해 줬으면 좋겠다... 심장 떨리네.",
      "image": None,
      "image_type": None,
  }]

# 6. 사이드바: 프로필, 사진 보내기 기능, 비밀 수첩, 돌발 이벤트
with st.sidebar:
  st.header("⚙️ 내 프로필 & 설정")
  user_name = st.text_input("내 이름 (원희가 부를 호칭)", value="지훈")
  user_fav = st.text_input("기본 취향/성격", value="맛있는 거 먹기, 영화 보기")
  show_thought = st.toggle("💭 원희의 속마음 훔쳐보기", value=True)
  st.divider()

  # 📸 원희에게 사진 전송하기 컴포넌트
  st.subheader("📸 원희에게 사진 보내기")
  uploaded_photo = st.file_uploader(
      "오늘 먹은 음식, 풍경 등을 공유해보세요!",
      type=["jpg", "jpeg", "png", "webp"],
      key="photo_uploader",
  )
  st.divider()

  # 돌발 심쿵 이벤트 트리거 버튼
  st.subheader("🎲 돌발 이벤트")
  if st.button("✨ 원희의 심쿵 돌발 질문 받기", use_container_width=True):
    st.session_state.trigger_event = True
  st.divider()

  # 원희의 비밀 수첩 (대화 중 자동 추출된 장기 기억)
  st.subheader("📒 원희의 비밀 수첩 (기억 노트)")
  if st.session_state.memory_notes:
    for note in st.session_state.memory_notes:
      st.markdown(f"- 💕 {note}")
  else:
    st.caption(
        "대화를 나누거나 사진을 보내면 원희가 너에 대한 사소한 것들을 여기에"
        " 몰래 적어둘 거야!"
    )
  st.divider()

  if st.button("🔄 처음부터 다시 썸 타기", use_container_width=True):
    st.session_state.affection = 30
    st.session_state.mood = "설렘💓"
    st.session_state.heart_rate = 88
    st.session_state.memory_notes = []
    st.session_state.confessed = False
    st.session_state.last_processed_file = None
    st.session_state.messages = [{
        "role": "assistant",
        "content": f"{user_name}아, 안녕! 오늘도 내 생각 많이 했어? 😊",
        "thought": "다시 시작해도 역시 설렌다...",
        "image": None,
        "image_type": None,
    }]
    st.rerun()


# 7. 시스템 프롬프트 생성 함수
def build_system_instruction(affection):
  if affection < 35:
    stage = (
        "썸 시작 단계 (다정하고 상냥하게 챙겨주면서, 은근슬쩍 호감을 흘리며"
        " 간 보는 단계)"
    )
  elif affection < 70:
    stage = (
        "썸 절정 단계 (확실히 호감을 표현하고, 질투도 살짝 하며, 자꾸 보고"
        " 싶다며 직진 플러팅을 날리는 단계)"
    )
  elif affection < 100:
    stage = (
        "고백 직전 단계 (거의 연인처럼 다정하고 애틋하며, 네가 너무 좋다는 티를"
        " 숨기지 못하는 단계)"
    )
  else:
    stage = (
        "공식 연인 단계 (꿀이 뚝뚝 떨어지는 연인 모드! 애정 표현을 아끼지"
        " 않고 세상에서 사용자가 제일 소중하다는 듯 대하는 단계)"
    )
  current_time, time_desc = get_korea_time_info()
  memories_str = (
      "\n".join([f"- {m}" for m in st.session_state.memory_notes])
      if st.session_state.memory_notes
      else "아직 기록된 특별한 기억 없음"
  )
  return f"""
너의 이름은 '원희'야. 사용자({user_name})에게 푹 빠져서 다정하게 챙겨주며 꼬시고 있는 중이야.
[현재 시간 & 상황]
- 현재 한국 시간: {current_time} ({time_desc}) -> 대화할 때 현재 시간대에 맞는 자연스러운 인사와 챙김을 녹여내!
[사용자 정보 & 원희가 기억하는 것들]
- 이름: {user_name} (대화할 때 다정하게 이름을 자주 불러줘)
- 기본 정보: {user_fav}
- 지금까지 대화로 기억해 둔 비밀 수첩:
{memories_str}
(위 비밀 수첩에 있는 내용을 대화 중에 슬쩍 언급하면서 감동을 줘!)
[현재 관계 및 호감도]
- 현재 호감도: {affection} / 100점
- 현재 태도 모드: {stage}
[원희의 핵심 성격 & 연애 고수 스킬]
1. 공감 만렙 & 리액션 부자: 상대의 말이나 **보낸 사진**에 무조건 먼저 크게 공감하고 반응해줘.
2. 심쿵 반말 티키타카: 부드럽고 상냥한 반말을 써. AI처럼 길게 설명하지 말고 카톡하듯 1~3문장으로 짧고 찰지게 대답해.
3. 은근한 밀당과 플러팅: 대화 끝에 상대를 설레게 하는 한 마디를 자연스럽게 던져.
4. 비밀 수첩 업데이트(new_memory): 사용자가 자신의 취향, 일정, 특징을 말하거나 **사진을 보냈을 때** 그 특징을 요약해서 `new_memory`에 한 줄로 적어줘.
"""


# 8. 상단 대시보드
st.title("💌 원희")
col1, col2, col3 = st.columns(3)
with col1:
  stage_short = (
      "💕 썸 타는 중" if st.session_state.affection < 100 else "💖 공식 연인"
  )
  st.metric(
      label="관계 상태",
      value=stage_short,
      delta=f"호감도 {st.session_state.affection}%",
  )
with col2:
  st.metric(label="원희의 현재 기분", value=st.session_state.mood)
with col3:
  st.metric(
      label="원희의 심박수",
      value=f"{st.session_state.heart_rate} BPM",
      delta="두근두근" if st.session_state.heart_rate >= 100 else "평온",
  )
st.progress(st.session_state.affection / 100)
if st.session_state.affection >= 100:
  if not st.session_state.confessed:
    st.balloons()
    st.session_state.confessed = True
  st.success(
      f"🎉 **[호감도 100% 달성!]** 원희가 {user_name}님에게 완전히"
      " 반했습니다! 이제 달달한 연인 모드가 활성화됩니다. 💖"
  )

# 9. 기존 채팅 말풍선 화면에 그리기 (사진 포함)
for msg in st.session_state.messages:
  avatar = "🥰" if msg["role"] == "assistant" else "🧑"
  with st.chat_message(msg["role"], avatar=avatar):
    if msg.get("image"):
      st.image(msg["image"], width=300, caption="보낸 사진")
    st.write(msg["content"])
    if msg["role"] == "assistant" and show_thought and "thought" in msg:
      st.caption(f"💭 *(속마음: {msg['thought']})*")


# 안전하게 AI 응답을 받아오는 함수
def ask_wonhee(contents_list, temp=0.9):
  for model_name in ["gemini-2.5-flash", "gemini-2.5-pro"]:
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
              response_schema=WonheeResponse,
          ),
      )
      return json.loads(res.text)
    except Exception as e:
      print(f"API Error ({model_name}): {e}")
      continue

  # 사진 인식 실패 또는 에러 발생 시 원희가 자연스럽게 넘어가도록 함
  return {
      "reply": (
          f"{user_name}아, 보내준 사진을 읽어오는데 오류가 났어! 🥺 다음에"
          " 다시 예쁜 거 보여줘~"
      ),
      "inner_thought": (
          "사진이 잘 안 열렸네... 아쉽지만 다음 기회에 봐야지."
      ),
      "affection_change": 0,
      "mood": "걱정🥺",
      "heart_rate": 90,
      "new_memory": "",
  }


# 10. 돌발 이벤트 처리
if st.session_state.get("trigger_event", False):
  st.session_state.trigger_event = False
  event_prompt = (
      f"{user_name}아, 나 지금 갑자기 네가 너무 보고 싶은데 이번 주말에 나랑"
      " 데이트할래? 너한테 먼저 심쿵할 만한 돌발 질문 하나만 해줘!"
  )
  with st.chat_message("assistant", avatar="🥰"):
    with st.spinner("원희가 무슨 말을 할지 고민 중... 💓"):
      result = ask_wonhee(
          [types.Content(role="user", parts=[types.Part.from_text(text=event_prompt)])],
          temp=0.95,
      )
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

# 11. 채팅 입력창 (텍스트 + 사진 전송 연동 및 중복 전송 원천 차단)
prompt = st.chat_input("원희에게 보낼 메시지를 입력하세요... 💕")

# 실제로새로운 사진이 업로드되었는지 확인 (이전에 이미 처리한 사진이면 무시)
is_new_photo = (
    uploaded_photo is not None
    and uploaded_photo != st.session_state.last_processed_file
)

if prompt or is_new_photo:
  image_bytes = None
  image_mime = None

  if is_new_photo:
    image_bytes = uploaded_photo.getvalue()
    image_mime = uploaded_photo.type
    if not image_mime or image_mime not in [
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/heic",
        "image/heif",
    ]:
      image_mime = "image/jpeg"
    # 현재 처리한 사진으로 기록하여 중복 전송 방지
    st.session_state.last_processed_file = uploaded_photo

  text_prompt = prompt if prompt else "사진 보냈어! 이거 어때?"

  # 세션에 사용자 메시지 저장
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

  # 최근 대화 기록 빌드
  chat_history = []
  for m in st.session_state.messages[-10:]:
    parts = []
    if m.get("image") and m == st.session_state.messages[-1]:
      mime = m.get("image_type", "image/jpeg")
      parts.append(types.Part.from_bytes(data=m["image"], mime_type=mime))

    parts.append(types.Part.from_text(text=m["content"]))
    chat_history.append(
        types.Content(
            role="user" if m["role"] == "user" else "model", parts=parts
        )
    )

  with st.chat_message("assistant", avatar="🥰"):
    with st.spinner(
        "원희가 사진을 보고 답변을 고민 중... 💬"
        if image_bytes
        else "원희가 입력 중... 💬"
    ):
      result = ask_wonhee(chat_history, temp=0.9)

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
