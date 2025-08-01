import streamlit as st
import random
from collections import defaultdict

st.set_page_config(page_title="🏸 Badminton Match Shuffler", layout="centered")

# --- Session State Initialization ---
if "players" not in st.session_state:
    st.session_state.players = []
if "waiting_players" not in st.session_state:
    st.session_state.waiting_players = []
if "match_history" not in st.session_state:
    st.session_state.match_history = []
if "current_match" not in st.session_state:
    st.session_state.current_match = []
if "match_count" not in st.session_state:
    st.session_state.match_count = 0
if "wins" not in st.session_state:
    st.session_state.wins = defaultdict(int)
if "match_played" not in st.session_state:
    st.session_state.match_played = defaultdict(int)
if "newly_joined_players" not in st.session_state:
    st.session_state.newly_joined_players = {}
if "cooldown_players" not in st.session_state:
    st.session_state.cooldown_players = {}
if "player_joined_match_number" not in st.session_state:
    st.session_state.player_joined_match_number = {}

# --- Helper Functions ---
def is_player_on_cooldown(player):
    return st.session_state.cooldown_players.get(player, 0) > 0

def get_available_players():
    all_players = set(st.session_state.players)
    busy_players = set(p for team in st.session_state.current_match for p in team)
    available = list(all_players - busy_players)
    return available

def start_new_match():
    available_players = get_available_players()
    if len(available_players) < 4:
        return

    st.session_state.match_count += 1

    # Cooldown handling
    for p in list(st.session_state.cooldown_players):
        if st.session_state.cooldown_players[p] > 0:
            st.session_state.cooldown_players[p] -= 1
        if st.session_state.cooldown_players[p] <= 0:
            del st.session_state.cooldown_players[p]

    # Identify newly added players
    newly_prioritized = [p for p in available_players if st.session_state.match_count - st.session_state.player_joined_match_number.get(p, 0) <= 2]
    regular_pool = [p for p in available_players if p not in newly_prioritized and not is_player_on_cooldown(p)]

    if len(newly_prioritized) >= 4:
        selected = random.sample(newly_prioritized, 4)
    elif len(newly_prioritized) >= 2 and len(regular_pool) >= (4 - len(newly_prioritized)):
        selected = newly_prioritized + random.sample(regular_pool, 4 - len(newly_prioritized))
    else:
        full_pool = [p for p in available_players if not is_player_on_cooldown(p)]
        selected = random.sample(full_pool, 4)

    random.shuffle(selected)
    team_a = selected[:2]
    team_b = selected[2:]
    st.session_state.current_match = [team_a, team_b]

    # Track match history
    st.session_state.match_history.append((team_a, team_b))
    for p in selected:
        st.session_state.match_played[p] += 1
        # Check if player should go into cooldown after 2 matches
        if st.session_state.match_count - st.session_state.player_joined_match_number.get(p, 0) == 2:
            st.session_state.cooldown_players[p] = 2

def update_after_match(winning_team):
    for player in winning_team:
        st.session_state.wins[player] += 1
    st.session_state.waiting_players = [p for team in st.session_state.current_match for p in team]
    st.session_state.current_match = []

def reset_app():
    st.session_state.players = []
    st.session_state.waiting_players = []
    st.session_state.match_history = []
    st.session_state.current_match = []
    st.session_state.match_count = 0
    st.session_state.wins = defaultdict(int)
    st.session_state.match_played = defaultdict(int)
    st.session_state.newly_joined_players = {}
    st.session_state.cooldown_players = {}
    st.session_state.player_joined_match_number = {}

# --- UI ---
st.title("🏸 Badminton Match Shuffler")

with st.sidebar:
    st.header("👥 Players")
    new_player = st.text_input("Add Player")
    if st.button("➕ Add") and new_player and new_player not in st.session_state.players:
        st.session_state.players.append(new_player)
        st.session_state.waiting_players.append(new_player)
        st.session_state.player_joined_match_number[new_player] = st.session_state.match_count
        st.rerun()

    if st.button("🔁 Reset App"):
        reset_app()
        st.rerun()

if not st.session_state.current_match:
    start_new_match()
    st.rerun()

st.header("🎮 Current Match")
team_a, team_b = st.session_state.current_match
st.subheader("🅰️ Team A")
st.write(", ".join(team_a))
st.subheader("🅱️ Team B")
st.write(", ".join(team_b))

if st.button("🏆 Team A Wins"):
    update_after_match(team_a)
    st.rerun()
if st.button("🏆 Team B Wins"):
    update_after_match(team_b)
    st.rerun()

st.markdown("---")
st.header("📊 Matches Played")
for p in st.session_state.players:
    matches = st.session_state.match_played[p]
    wins = st.session_state.wins[p]
    status = "🧊 Cooldown" if is_player_on_cooldown(p) else "🟢 Active"
    st.markdown(f"- **{p}**: {matches} matches | 🏆 {wins} wins {status}")

st.markdown("---")
st.header("🧘 Waiting Players")
waiting = [p for p in st.session_state.waiting_players if p not in team_a + team_b]
st.markdown(" ".join([f"`{p}`" for p in waiting]) or "_None_")
