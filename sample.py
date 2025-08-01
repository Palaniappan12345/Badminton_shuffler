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
if "match_counts" not in st.session_state:
    st.session_state.match_counts = defaultdict(int)
if "win_counts" not in st.session_state:
    st.session_state.win_counts = defaultdict(int)
if "last_played_time" not in st.session_state:
    st.session_state.last_played_time = defaultdict(lambda: -1)
if "removed_players" not in st.session_state:
    st.session_state.removed_players = []
if "newly_joined_players" not in st.session_state:
    st.session_state.newly_joined_players = {}
if "cooldown_players" not in st.session_state:
    st.session_state.cooldown_players = {}
if "match_number" not in st.session_state:
    st.session_state.match_number = 0
if "player_names_input" not in st.session_state:
    st.session_state.player_names_input = {}

def is_player_on_cooldown(player):
    return st.session_state.cooldown_players.get(player, 0) > 0

def get_active_players():
    return [p for p in st.session_state.players if p not in st.session_state.removed_players]

def reset_all():
    for key in list(st.session_state.keys()):
        del st.session_state[key]

def add_new_players(new_players_input):
    new_players = [p.strip() for p in new_players_input.split(",") if p.strip()]
    for p in new_players:
        if p in st.session_state.players:
            continue
        st.session_state.players.append(p)
        st.session_state.waiting_players.append(p)
        st.session_state.newly_joined_players[p] = st.session_state.match_number
        st.session_state.match_counts[p] = 0
        st.session_state.win_counts[p] = 0
        st.session_state.last_played_time[p] = -1
        st.session_state.cooldown_players[p] = 0

def submit_match_result(winner_choice):
    team_a, team_b = st.session_state.current_match
    winning_team = team_a if winner_choice == "A" else team_b
    losing_team = team_b if winner_choice == "A" else team_a

    for p in team_a + team_b:
        st.session_state.match_counts[p] += 1
        st.session_state.last_played_time[p] = st.session_state.match_number

    for p in winning_team:
        st.session_state.win_counts[p] += 1

    for p in losing_team:
        if p in st.session_state.waiting_players:
            st.session_state.waiting_players.remove(p)
    for p in winning_team:
        if p not in st.session_state.removed_players:
            st.session_state.waiting_players.append(p)

    st.session_state.match_history.append({
        "team_a": team_a,
        "team_b": team_b,
        "winner": "A" if winner_choice == "A" else "B"
    })

    for p in list(st.session_state.cooldown_players.keys()):
        if st.session_state.cooldown_players[p] > 0:
            st.session_state.cooldown_players[p] -= 1

    st.session_state.match_number += 1
    st.session_state.current_match = []
    start_new_match()

def start_new_match():
    available = [p for p in st.session_state.waiting_players if p not in st.session_state.removed_players and not is_player_on_cooldown(p)]
    if len(available) < 4:
        st.session_state.current_match = []
        return

    new_players = [p for p in available if st.session_state.newly_joined_players.get(p, -1) >= 0 and st.session_state.match_number - st.session_state.newly_joined_players[p] < 2]
    others = [p for p in available if p not in new_players]
    random.shuffle(new_players)
    random.shuffle(others)
    prioritized = new_players + others
    selected = prioritized[:4]
    random.shuffle(selected)
    team_a = selected[:2]
    team_b = selected[2:]
    st.session_state.current_match = (team_a, team_b)

    for p in new_players:
        if st.session_state.match_counts[p] >= 2:
            st.session_state.cooldown_players[p] = 2
            st.session_state.newly_joined_players[p] = -1

# --- UI Starts Here ---
st.title("🏸 Badminton Match Shuffler")

if not st.session_state.players:
    st.header("👥 Add Players")
    st.session_state.player_count = st.slider("Number of players", 4, 9, value=4)
    names = []
    for i in range(1, st.session_state.player_count + 1):
        name = st.text_input(f"Player {i} Name", key=f"player_{i}")
        st.session_state.player_names_input[f"player_{i}"] = name
        names.append(name)
    if st.button("✅ Start Match"):
        player_list = [name.strip() for name in names if name.strip()]
        if len(player_list) != len(set(player_list)):
            st.error("⚠️ Duplicate names found!")
        elif len(player_list) < 4:
            st.warning("At least 4 valid player names needed.")
        else:
            st.session_state.players = player_list
            st.session_state.waiting_players = player_list.copy()
            for name in player_list:
                st.session_state.newly_joined_players[name] = -1
                st.session_state.cooldown_players[name] = 0
            start_new_match()
            st.rerun()
else:
    st.header("🎮 Current Match")
    if st.session_state.current_match:
        team_a, team_b = st.session_state.current_match
        team_a = [p for p in team_a if p not in st.session_state.removed_players]
        team_b = [p for p in team_b if p not in st.session_state.removed_players]
        if len(team_a) < 2 or len(team_b) < 2:
            st.warning("❗ Current match has removed players. Resetting match.")
            start_new_match()
            st.rerun()
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 🅰️ Team A")
                st.success(", ".join(team_a))
            with col2:
                st.markdown("### 🅱️ Team B")
                st.info(", ".join(team_b))
            winner_choice = st.radio("🏆 Who won?", ["A", "B"], horizontal=True)
            if st.button("Submit Result"):
                submit_match_result(winner_choice)
                st.rerun()
    else:
        st.info("⚠️ No active match. Waiting to start.")

    st.markdown("---")
    st.header("➕ Add New Players")
    new_players_input = st.text_input("Enter names (comma-separated)", key="new_players_input")
    if st.button("Add Players"):
        add_new_players(new_players_input)

    st.markdown("---")
    st.header("❌ Remove Players")
    removable_players = get_active_players()
    players_to_remove = st.multiselect("Select players to remove", removable_players)
    if st.button("Remove Selected Players"):
        if players_to_remove:
            for p in players_to_remove:
                if p not in st.session_state.removed_players:
                    st.session_state.removed_players.append(p)
                if p in st.session_state.waiting_players:
                    st.session_state.waiting_players.remove(p)
            st.success(f"✅ Removed: {', '.join(players_to_remove)}")
            st.rerun()

    st.markdown("---")
    st.header("🧘 Waiting Players")
    waiting = [p for p in st.session_state.waiting_players if p not in st.session_state.removed_players and not is_player_on_cooldown(p)]
    st.markdown(" ".join([f"`{p}`" for p in waiting]) or "_None_")

    st.markdown("---")
    st.header("❌ Removed Players")
    st.markdown(" ".join([f"`{p}`" for p in st.session_state.removed_players]) or "_None_")

    st.markdown("---")
    st.header("📊 Matches Played")
    all_players = st.session_state.players + st.session_state.removed_players
    for p in all_players:
        match_count = st.session_state.match_counts.get(p, 0)
        win_count = st.session_state.win_counts.get(p, 0)
        status = "🟢 Active" if p not in st.session_state.removed_players else "❌ Removed"
        st.markdown(f"- **{p}**: {match_count} matches | 🏆 {win_count} wins &nbsp;&nbsp;{status}")

    st.markdown("---")
    st.header("📜 Match History")
    if st.session_state.match_history:
        for i, m in enumerate(st.session_state.match_history, 1):
            st.markdown(f"**Match {i}:** {m['team_a']} vs {m['team_b']} → 🏆 **Winner:** {m['winner']}")
    else:
        st.write("_No matches yet._")

    st.markdown("---")
    st.button("🔄 Reset All", on_click=lambda: (reset_all(), st.rerun()))
