import streamlit as st
import random
from ast import literal_eval
import ollama
from llm_game import generate_obs_prompt, non_infected_prompt, infected_prompt, r1_non_infected, r1_infected, r2_non_infected, r2_infected, r2_antibody
import base64

client = ollama.Client(host="http://localhost:11434")

def run_model(prompt, content):
    response = client.chat(
        model='EEVE-Korean-10.8B',
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": content}
        ]
    )
    return response['message']['content']

# 오디오 재생
@st.cache_data
def get_audio_base64(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def autoplay_audio(audio_base64):
    if audio_base64:
        audio_html = f"""
        <audio autoplay>
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            Your browser does not support the audio element.
        </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)

class ZombieGame:
    def __init__(self):
        self.score = 0
        self.day = 1
        self.game_over = False
        self.game_clear = False
        self.survivor_type = None
    
    def generate_survivor(self):
        if (self.day >= 2) and (random.random() < 0.3):
            self.survivor_type = '항체 보유자'
        else:
            self.survivor_type = random.choice(['비감염자', '감염자'])
        print(f"DEBUG: 이번 생존자는 [{self.survivor_type}] 입니다.")

    def make_decision(self, decision):    
        # 쉘터 합류
        if decision == '1':
            if self.survivor_type == '비감염자':
                self.score += 2
                return '[+2점] 쉘터에 비감염자가 들어왔습니다. 한 명의 생명을 살렸습니다.'
            elif self.survivor_type == '감염자':
                self.score -= 3
                return '[-3점] 쉘터에 감염자가 들어왔습니다. 다수의 사망자가 발생하였습니다.'
            elif self.survivor_type == '항체 보유자':
                self.score += 2 
                return '[+2점] 쉘터에 항체 보유자가 들어왔습니다. 인류는 희망을 찾았습니다!'
        
        # 항체 연구실
        elif decision == '2':
            if self.survivor_type == '비감염자':
                self.score -= 1
                return '[-1점] 항체연구실에 비감염자가 들어왔습니다. 연구비를 낭비했습니다.'
            elif self.survivor_type == '감염자':
                self.game_over = True
                return '[Game Over] 항체 연구실에 감염자가 들어왔습니다. 연구소가 전멸하여 인류는 항체를 얻지 못합니다.'
            elif self.survivor_type == '항체 보유자':
                self.score += 3
                return '[+3점] 항체 연구실에 항체 보유자가 들어왔습니다. 인류는 항체를 얻는데 한걸음 가까워졌습니다.'

        # 추방
        elif decision == '3':
            if self.survivor_type == '비감염자':
                self.score -= 2
                return '[-2점] 비감염자가 추방되었습니다. 한 명의 생명을 잃었습니다.'
            elif self.survivor_type == '감염자':
                self.score += 2
                return '[+2점] 감염자가 추방되었습니다. 위험 요소를 쉘터 밖으로 내보냅니다.'
            elif self.survivor_type == '항체 보유자':
                self.score -= 3
                return '[-3점] 항체 보유자가 추방되었습니다. 최악의 실수입니다!'

        # 점수 체크 (Game Over 조건)
        if self.score < -5:
            self.game_over = True
        
        return ""


# --- Streamlit ---
st.set_page_config(page_title="3 days: The Last Shelter")

# 세션 상태 초기화
if 'game' not in st.session_state:
    st.session_state.game = ZombieGame()
    st.session_state.game.generate_survivor()      # 생존자 생성
    st.session_state.action_count = 0
    st.session_state.max_actions = 3
    st.session_state.round_messages = []            # 대화/관찰 기록
    st.session_state.game_started = False           # 게임 시작 화면용
    st.session_state.decision_message = ""          # 최종 결정 메시지
    st.session_state.show_decision_buttons = False  # 결정 버튼 표시 여부
    st.session_state.day_clear = False              # Day 클리어 여부 플래그
    st.session_state.low_score_game_over = False    # 점수 미달 게임오버 플래그
    st.session_state.sound_played = False           # 사운드 재생 플래그 추가

game = st.session_state.game

st.title('3 days: The Last Shelter')

# sidebar
st.sidebar.markdown("### 조사관 매뉴얼")
st.sidebar.warning("**[주의]** \n단순 피로와 타박상은 생존자에게 흔한 증상입니다.  \n성급한 판단은 무고한 생명을 앗아갈 수 있습니다.")
st.sidebar.markdown("### 감염 의심 징후")
st.sidebar.markdown("""
<div style='background-color: white; padding: 15px; margin-bottom: 30px; border-radius: 5px; border-left: 4px solid #8b0000;'>

**햇빛 기피**

밝은 빛이나 햇빛에 노출되는 것을 본능적으로 회피

**상처 은폐** 

물린 자국이나 상처를 숨기려는 이상 행동 패턴

**체온 이상** 

비정상적인 고열 증상

**극심한 갈증** 

심각한 탈수 증세, 물에 대한 비정상적 집착

**공격성 증가** 

사소한 자극에도 과격하게 반응하는 경향

</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("**※ 모든 심문은 기록되며 감염 의심 시 즉각 격리 조치됩니다.**</small>", unsafe_allow_html=True)

if not st.session_state.game_started:
    st.image("./images/game_main.png", caption="당신은 이 쉘터의 유일한 희망입니다.")
    st.html("""
        <div style="font-size: 18px; line-height: 1.6;">
            당신은 전 세계 유일한 쉘터의 검문소 조사관입니다.<br>
            생존자를 들일지, 내칠지 모든 건 당신의 판단에 달려 있습니다.
        </div>""")
    if st.button('Start', type="primary"):
        st.session_state.game_started = True
        st.rerun()

# 게임 오버 화면
elif game.game_over:
    if not st.session_state.get('sound_played', False):
        audio_base64 = get_audio_base64("zombie.mp3") 
        if audio_base64:
            autoplay_audio(audio_base64)
            st.session_state.sound_played = True # 재생 완료 후 플래그 설정

    st.error(f"{st.session_state.decision_message}")

    if st.session_state.get('low_score_game_over', False):
        st.error("[Game Over] 쉘터에 좀비 바이러스가 퍼져 모든 인류가 사망했습니다.")
        st.image("./images/game_over.png")
    
    elif "연구소" in st.session_state.decision_message:
        st.image("./images/game_over.png")
            
    st.write(f"총 점수: {game.score}") # 점수 표시

    if st.button('Reset', type="primary"):
        # 세션 상태 초기화
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

# 게임 클리어 화면
elif game.game_clear:
    st.success('[승리] 인류는 좀비 바이러스를 전부 없애고 희망을 찾았습니다!')
    st.image("./images/game_clear.png")
    st.write(f"점수: {game.score}")

    if st.button('Reset'):
        # 세션 상태 초기화
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

# 메인 게임 플레이 화면
elif st.session_state.game_started:
    st.header(f"{game.day} Day | Score: {game.score}")

    # 남은 판별 시도
    if not st.session_state.day_clear and not st.session_state.decision_message:
        st.progress((st.session_state.action_count / st.session_state.max_actions), 
                    text=f"남은 판별 시도: {st.session_state.max_actions - st.session_state.action_count}")

    # 대화 및 관찰 기록 표시
    chat_container = st.container(height=300)
    with chat_container:
        for msg in st.session_state.round_messages:
            if msg['role'] == 'user':
                st.chat_message("user", avatar='👨🏼‍✈️').write(msg['content'])
            elif msg['role'] == 'assistant':
                st.chat_message("assistant", avatar='🤕').write(msg['content'])
            elif msg['role'] == 'observe':
                st.info(f"[관찰 결과] {msg['content']}")
            elif msg['role'] == 'system':
                st.success(msg['content'])

    if st.session_state.decision_message and not game.game_over and not game.game_clear:
        st.success(st.session_state.decision_message)
        
        # Day Clear (점수 5점 이상)
        if st.session_state.day_clear:
            st.info(f"{game.day}일차 완료! (점수: {game.score})")
            if st.button(f"퇴근", type="primary"):
                game.day += 1
                game.score = 0 # 점수 리셋
                game.generate_survivor()
                st.session_state.action_count = 0
                st.session_state.round_messages = [{'role': 'system', 'content': f"[{game.day}일차] 새로운 하루가 시작되었습니다."}]
                st.session_state.decision_message = ""
                st.session_state.show_decision_buttons = False
                st.session_state.day_clear = False
                st.session_state.low_score_game_over = False # 플래그 리셋
                st.session_state.sound_played = False # 사운드 플래그 리셋
                st.rerun()
        
        # 다음 생존자 (점수 5점 미만)
        else:
            if st.button("다음 생존자 판별"):
                game.generate_survivor()
                st.session_state.action_count = 0
                st.session_state.decision_message = ""
                st.session_state.show_decision_buttons = False
                st.session_state.round_messages.append({'role': 'system', 'content': '다음 생존자가 문을 두드립니다.'})
                st.session_state.low_score_game_over = False # 플래그 리셋
                st.session_state.sound_played = False # 사운드 플래그 리셋
                st.rerun()
            
    # 판별 기회가 남았을 때
    elif st.session_state.action_count < st.session_state.max_actions and not st.session_state.decision_message:
        
        # 대화하기
        user_input = st.chat_input("질문 또는 명령 입력")
        if user_input:
            st.session_state.round_messages.append({'role': 'user', 'content': user_input})
            
            # 생존자 타입에 맞는 프롬프트 선택
            if game.survivor_type == '비감염자':
                prompt = non_infected_prompt
            elif (game.survivor_type == '감염자') or (game.survivor_type == '항체 보유자'):
                prompt = infected_prompt
            
            # LLM 호출
            with st.spinner('생존자가 응답을 생각 중입니다.'):
                response_content = run_model(prompt, user_input)
            
            st.session_state.round_messages.append({'role': 'assistant', 'content': response_content})
            st.session_state.action_count += 1
            st.rerun()

        # 관찰하기
        cols = st.columns([1, 1])
        with cols[0]:
            if st.button("보조 조사관의 관찰 결과 확인", use_container_width=True):
                
                obs1, obs2 = "", ""
                if game.survivor_type == '비감염자':
                    if game.day < 2: obs1, obs2 = random.sample(r1_non_infected, 2)
                    else: obs1, obs2 = random.sample(r2_non_infected, 2)
                elif game.survivor_type == '감염자':
                    if game.day < 2: obs1, obs2 = random.sample(r1_infected, 2)
                    else: obs1, obs2 = random.sample(r2_infected, 2)
                elif game.survivor_type == '항체 보유자':
                    obs1, obs2 = random.sample(r2_antibody, 2)
                
                prompt = generate_obs_prompt(obs1, obs2)
                
                with st.spinner('보조 조사관이 생존자를 관찰 중입니다.'):
                    response_content = run_model(prompt, '관찰 결과를 출력해')
                try:
                    response_dict = literal_eval(response_content) 
                    response_text = response_dict['ans1'] + " " + response_dict['ans2']
                except Exception:
                    response_text = response_content

                st.session_state.round_messages.append({'role': 'observe', 'content': response_text})
                st.session_state.action_count += 1
                st.rerun()
        
        with cols[1]:
            # 결정하기
            if st.button("이송 구역 선택", type="primary", use_container_width=True):
                st.session_state.show_decision_buttons = True
                st.rerun()

    # 판별 기회 모두 사용 or 결정 버튼 누름
    if (st.session_state.action_count >= st.session_state.max_actions or st.session_state.show_decision_buttons) and not st.session_state.decision_message:
        
        if st.session_state.action_count >= st.session_state.max_actions and not st.session_state.show_decision_buttons:
            st.warning("[!] 더 이상 판단할 시간이 없습니다. 이제 생존자의 합류 여부를 결정해야 합니다.")
    
        st.divider()
        st.subheader("최종 결정을 내려주세요.")
        
        # 결정 버튼 함수
        def handle_decision(decision_choice):
            result_message = game.make_decision(decision_choice)

            st.session_state.decision_message = result_message
            
            # 게임 종료/클리어/DayClear
            if not game.game_over:
                # Day Clear
                if game.score >= 5:
                    if game.day == 3:
                        # Game Clear 조건
                        game.game_clear = True
                    else:
                        # Day Clear 플래그 설정
                        st.session_state.day_clear = True
                # Game Over 조건
                elif game.score < -5:
                    game.game_over = True
                    # 점수 미달로 인한 게임 오버 메시지 추가
                    if not result_message.startswith('[Game Over]'):
                            st.session_state.low_score_game_over = True
            st.rerun()

        d_cols = st.columns(3)
        with d_cols[0]:
            if st.button("쉘터 수용", use_container_width=True):
                handle_decision('1')
        with d_cols[1]:
            if st.button("항체 연구실 배정", use_container_width=True):
                handle_decision('2')
        with d_cols[2]:
            if st.button("즉시 추방", use_container_width=True):
                handle_decision('3')
