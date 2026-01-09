import streamlit as st
import time
import random
from openai import OpenAI
import math

# CONFIG 
MAX_HP = 100
PLAYER_DAMAGE = 10
BOSS_DAMAGE = 15
QUESTION_TIME = 10

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# STYLING 
st.markdown("""
<style>
body {
    background-color: #0e0e0e;
    color: #e6e6e6;
}

/* HP boxes */
.hp-box {
    background: #ffffff;
    color: #111111;
    padding: 14px;
    border-radius: 14px;
    border: 2px solid #ddd;
    font-size: 16px;
}

/* Boss dialogue box */
.boss-box {
    background: #ffffff;
    color: #111111;
    padding: 26px;
    border-radius: 18px;
    border: 3px solid #a00000;
    text-align: center;
    font-size: 22px;
    box-shadow: 0 0 20px rgba(255,0,0,0.3);
}

/* Buttons */
.stButton > button {
    border-radius: 14px;
    padding: 16px;
    font-size: 18px;
    font-weight: bold;
    transition: 0.15s ease-in-out;
}

.stButton > button:hover {
    transform: scale(1.04);
}
</style>
""", unsafe_allow_html=True)

# HELPERS 
def get_completion(prompt, model=st.secrets["OPENAI_MODEL_NAME"], api_key=client):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content

def distortion(message):
    glitch_chars = ["#", "@", "%", "&", "*", "~", "§", "∆", "¤"]
    result = []

    for ch in message:
        r = random.random()
        if ch.isalpha():
            if r < 0.2:
                result.append(ch.upper())
            elif r < 0.4:
                result.append(ch.lower())
            elif r < 0.45:
                result.append(random.choice(glitch_chars))
            else:
                result.append(ch)
        elif ch == " " and random.random() < 0.1:
            result.append("   ")
        else:
            result.append(ch)

    words = "".join(result).split()
    if random.random() < 0.3 and len(words) > 4:
        i = random.randint(0, len(words) - 2)
        words.insert(i, words[i])
    return " ".join(words)

def hp_bar(title, hp):
    st.markdown(f"**{title}: {hp}/{MAX_HP}**")
    if hp < 0:
        hp = 0
    st.progress(hp / MAX_HP)

def image(url):
    st.markdown(f'<div style="text-align:center;"><img src="{url}" width="400"></div>', unsafe_allow_html=True)

def calculate_score():
    player_hp = st.session_state.player_hp
    
    return round(player_hp)

# DEFAULT SESSION STATE
defaults = {
    "page": "home",
    "loading": False,
    "player_hp": MAX_HP,
    "boss_hp": MAX_HP,
    "new_choice": None,
    "question_id": 0,
    "topic": "Physics",
    "conversation": [{"role": "boss", "text": "Throughout heaven and earth, I alone am the honoured one."}],
    "options": ["Fight Back:correct", "Run Away:wrong", "Get Ready:correct", "Lock in: correct"],
    "chat_history": [],
    "boss_name": "",
    "phase": "awaiting_answer",
    "question_start_time": time.time(),
    "time_limit": QUESTION_TIME,
    "player_damage": PLAYER_DAMAGE,
    "boss_damage": BOSS_DAMAGE,
    "selected_answer": None
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# HOME PAGE
st.markdown("""
<style>
.stButton>button {
    background-color: #ff4b4b;  /* bright red */
    color: white;
    border-radius: 12px;
    padding: 12px 24px;
    font-size: 20px;
    font-weight: bold;
}
.stButton>button:hover {
    background-color: #ff1a1a;  /* darker red on hover */
    transform: scale(1.05);
}
</style>
""", unsafe_allow_html=True)

if st.session_state.page == "home":
    st.markdown("<h1 style='text-align:center;'>Boss Battle Simulator</h1>", unsafe_allow_html=True)

    image("https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExeGkwdnRhYnF2ZTRiaHJubzBjY3Fmc2RkNDdxYXJwYzYyeTRoZndicCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/tHQWHNkZcJzTdkh0Ym/giphy.gif")

    st.session_state.topic = st.text_input("Topic", st.session_state.topic, placeholder="Type the subject you want to battle with.")
    if len(st.session_state.topic) == 0:
        st.markdown(f"<p style='text-align:center;'>Your fate is uncertain...</p>", unsafe_allow_html=True)
    else:
        st.markdown(f"<p style='text-align:center;'>{st.session_state.topic} decides your fate.</p>", unsafe_allow_html=True)

    st.space("small")

    st.markdown("**Settings**")
    st.session_state.time_limit = st.slider("Time per question (seconds)", 5, 30, value=QUESTION_TIME)
    st.session_state.boss_damage = st.slider("Boss DMG", 1, 50, value=BOSS_DAMAGE)
    st.session_state.player_damage = st.slider("Your DMG", 1, 50, value=PLAYER_DAMAGE)

    st.space("small")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("▶ Start Battle", use_container_width=True):
            if len(st.session_state.topic) == 0:
                st.warning("Please enter a topic.")
            else:
                st.session_state.page = "game"
                st.session_state.player_hp = MAX_HP
                st.session_state.boss_hp = MAX_HP
                st.session_state.question_id = 0
                st.session_state.conversation = [{"role": "boss", "text": f"Throughout heaven and earth, I alone am the honoured one. Do you really think you can beat me at {st.session_state.topic}?"}]
                st.session_state.phase = "awaiting_answer"
                st.session_state.question_start_time = time.time()

# GAME PAGE 
elif st.session_state.page == "game":
    # Boss name generation
    if len(st.session_state.boss_name) == 0:
        try:
            st.session_state.boss_name = get_completion(f"""
            Generate me a spooky evil name for 'The Boss of {st.session_state.topic}'
            Reply with only the name. It must be a reference to the topic - {st.session_state.topic}.
            """)
        except Exception:
            st.session_state.boss_name = f"The Boss of {st.session_state.topic}"

    image("https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExbHA2bGJoZmFmYnV6c3JlcjZlc3Z2cG03YnAxMG85NXp6emd6MHZ3ZiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/inrMB0Hc82Q9Jt2QkG/giphy.gif")
    st.markdown(f"<h1 style='text-align:center;'>{st.session_state.boss_name}</h1>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        hp_bar("🧑 YOU", st.session_state.player_hp)
    with col2:
        hp_bar(f"👹 {st.session_state.boss_name}", st.session_state.boss_hp)

    st.markdown("---")

    boss_text = st.session_state.conversation[-1]["text"]
    st.markdown(f"""
    <div class="boss-box">
        ☠ <b>{distortion(boss_text)}</b> ☠
    </div>
    """, unsafe_allow_html=True)

    # TIMER LOGIC 
    timer_placeholder = st.empty()

    elapsed = time.time() - st.session_state.question_start_time
    remaining = max(0, int(st.session_state.time_limit - elapsed))
    progress = remaining / st.session_state.time_limit

    st.space(size="small")

    st.markdown(f"**Time Remaining: {remaining} seconds left**")
    st.progress(progress)

    st.space(size="small")

    if remaining == 0 and st.session_state.phase == "awaiting_answer":
        st.warning(f"Time Ran Out! -{st.session_state.boss_damage} damage.")
        st.session_state.player_hp -= st.session_state.boss_damage
        st.session_state.phase = "loading_next_question"

    # BUTTONS
    if st.session_state.phase == "awaiting_answer":
        for i, option in enumerate(st.session_state.options):
            text, result = option.rsplit(":", 1)
            if st.button(text, key=f"q{st.session_state.question_id}_opt{i}", use_container_width=True):
                st.session_state.selected_answer = i
                st.session_state.phase = "processing_answer"

    # PROCESS ANSWER 
    if st.session_state.phase == "processing_answer":
        _, result = st.session_state.options[st.session_state.selected_answer].rsplit(":", 1)
        if result == "correct":
            st.session_state.boss_hp -= st.session_state.player_damage
            st.success("✅ Correct!")
        else:
            st.session_state.player_hp -= st.session_state.boss_damage
            st.error("❌ Wrong!")

        st.session_state.player_hp = max(0, st.session_state.player_hp)
        st.session_state.boss_hp = max(0, st.session_state.boss_hp)
        st.session_state.selected_answer = None
        st.session_state.phase = "loading_next_question"

    # CHECK GAME OVER
    if st.session_state.player_hp == 0:
        st.error("You have been defeated.")
        st.session_state.page = "end_fail"
        st.rerun()
    if st.session_state.boss_hp == 0:
        st.success("Victory!")
        st.balloons()
        st.session_state.page = "end_victory"
        st.rerun()

    # LOAD NEXT QUESTION 
    if st.session_state.phase == "loading_next_question":
        st.session_state.question_id += 1
        st.session_state.loading = True
        st.session_state.new_choice = None
        st.session_state.question_start_time = time.time()

        # Generate next question
        with st.spinner("The boss is thinking..."):
            prompt = f"""
You are a boss specialised in {st.session_state.topic}.

Rules:
- Ask ONE question.
- Provide EXACTLY 4 answers.
- No commas in answers.
- End answers with :correct or :wrong.
- Output exactly 5 comma-separated items.
- Correct answer must be in the {random.randint(1,4)} postion

<Format>
'boss_question','a:correct','b:wrong','c:wrong','d:wrong'
</Format>

<EXAMPLES>
Answer in the 1 position -> 'What is the acceleration due to gravity on Earth?','9.8 m/s^2:correct','10 m/s^2:wrong','5 m/s^2:wrong','12 m/s^2:wrong'
Answer in the 2 position -> 'What is the capital of France?','London:wrong','Paris:correct','Berlin:wrong','Madrid:wrong'
Answer in the 3 position -> 'What is the largest planet in our solar system?','Venus:wrong','Mars:wrong','Jupiter:correct','Saturn:wrong'
Answer in the 4 position -> 'Who painted the Mona Lisa?','Michelangelo:wrong','Pablo Picasso:wrong','Vincent van Gogh:wrong','Leonardo da Vinci:correct'
</EXAMPLES>

Do not ask these following questions:
{st.session_state.chat_history}
"""
            try:
                response = get_completion(prompt)
                parts = [p.strip().strip("'\"") for p in response.split(",")]
                if len(parts) != 5:
                    raise ValueError("Bad model output")
                st.session_state.conversation.append({"role":"boss","text":parts[0]})
                st.session_state.options = parts[1:]
                st.session_state.chat_history.append(parts[0])
            except Exception:
                st.session_state.conversation.append({"role":"boss","text":"The boss is suddenly confused! Strike!"})
                st.session_state.options = ["ATTACK:correct","ATTACK:correct","ATTACK:correct","MISS:wrong"]
            finally:
                st.session_state.loading = False
                st.session_state.phase = "awaiting_answer"
                st.rerun()

if st.session_state.page.split("_")[0] == "end":
  if st.session_state.page.split("_")[1] == "victory":

    score = calculate_score()

    st.markdown("<h1 style='text-align:center; color:#39FF14;'>Victory!</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align:center; color:green;'>You made {st.session_state.boss_name} kneel in utter failure, crowning you the champion of {st.session_state.topic}.</h3>", unsafe_allow_html=True)

    image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExMmNodjRnZ2NqZ25uZnFtMG5hZ3NjcHU4dzlucmQxNjltNzk0d2pycyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/mCdhhsCLGluNi/giphy.gif")

    st.markdown(
    f"<div style='text-align:center; margin-top:20px; font-size:24px; color:#39FF14;'>Your Score: {score}/100</div>",
    unsafe_allow_html=True
    )

    st.markdown("<div style='text-align:center; margin-top:20px;'>Want to play again? Refresh to try again.</div>", unsafe_allow_html=True)

  if st.session_state.page.split("_")[1] == "fail":
    score = calculate_score()
      
    st.markdown("<h1 style='text-align:center; color:red;'>Defeat.</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align:center; color:#ff6666;'>{st.session_state.boss_name} walks away, knowing that he truly is the supreme king of {st.session_state.topic}.</h3>", unsafe_allow_html=True)

    image("https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExbGxqZTRsMXVoYmQ3dGJrOWNyemNqdDIzeTdwOTVtcXZmaTVjbnBhayZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/6ElPiQGynp3oAFPxij/giphy.gif")
    st.markdown(
    f"<div style='text-align:center; margin-top:20px; font-size:24px; color:gold;'>Your Score: {score}/100</div>",
    unsafe_allow_html=True
    )
    st.markdown("<div style='text-align:center; margin-top:20px;'>Better luck next time. Refresh to try again.</div>", unsafe_allow_html=True)
