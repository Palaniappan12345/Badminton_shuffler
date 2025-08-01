import streamlit as st
import random
from collections import defaultdict
from datetime import datetime

st.set_page_config(page_title="🏸 Badminton Match Shuffler", layout="centered")

# --- Session State Initialization ---
if "players" not in st.session_state:
    st.session_state.players = []
if "waiting_players" not in st.session_state:
    st.session_state.waiting_players = []
if "match_history" not in st.session_state:
    st.session_state.match_history = []
if "current_match" not in st.session_state:
    st.session_state.current_match = None
if "match_counts" not in st.session_state:
    st.session_state.match_counts = defaultdict(int)
if "win_counts" not in st.session_state:
    st.session_state.win_counts = defaultdict(int)
if "removed_players" not in st.session_state:
    st.session_state.removed_players = {}
if "last_winning_team" not in st.session_state:
    st.session_state.last_winning_team = []
if "last_played_time" not in st.session_state:
    st.session_state.last_played_time = defaultdict(lambda: datetime.min)
if "match_number" not in st.session_state:
    st.session_state.match_number = 0
if "newly_joined_players" not in st.session_state:
    st.session_state.newly_joined_players = defaultdict(int)
if "cooldown_players" not in st.session_state:
    st.session_state.cooldown_players = defaultdict(int)

# --- Helper Functions ---
def start_new_match():
    all_players = st.session_state.players.copy()
    if len(all_players) < 4:
        st.warning("Need at least 4 players.")
        return

    def pick_fair_four():
        def sort_key(p):
            if p in st.session_state.newly_joined_players:
                return (-1, st.session_state.last_played_time[p])  # priority for 2 matches
            return (st.session_state.match_counts[p], st.session_state.last_played_time[p])

        eligible_players = [
            p for p in all_players if st.session_state.cooldown_players.get(p, 0) == 0
        ]
        sorted_players = sorted(eligible_players, key=sort_key)
        return sorted_players[:4]

    selected = pick_fair_four()
    if len(selected) < 4:
        st.warning("Not enough eligible players (some are in cooldown).")
        return

    team_a = selected[:2]
    team_b = selected[2:]

    # Avoid repeating same winning team
    if (
        len(all_players) in [5, 6]
        and set(team_a) == set(st.session_state.last_winning_team)
    ):
        team_a, team_b = team_b, team_a

    st.session_state.current_match = (team_a, team_b)
    st.session_state.match_number += 1

    # Update match count and last played time
    for player in team_a + team_b:
        st.session_state.match_counts[player] += 1
        st.session_state.last_played_time[player] = datetime.now()

    # Clear cooldown players only if they did not play
    for p in list(st.session_state.cooldown_players.keys()):
        if p not in team_a + team_b:
            st.session_state.cooldown_players[p] -= 1
            if st.session_state.cooldown_players[p] <= 0:
                del st.session_state.cooldown_players[p]

def submit_match_result(winner_team):
    if not st.session_state.current_match:
        return

    team_a, team_b = st.session_state.current_match
    winner = team_a if winner_team == "A" else team_b
    loser = team_b if winner_team == "A" else team_a

    st.session_state.match_history.append(
        {
            "match": st.session_state.match_number,
            "team_a": team_a,
            "team_b": team_b,
            "winner": winner,
        }
    )

    for player in winner:
        st.session_state.win_counts[player] += 1

    st.session_state.last_winning_team = winner
    st.session_state.current_match = None

    # Handle newly joined cooldown tracking
    for player in team_a + team_b:
        if player in st.session_state.newly_joined_players:
            st.session_state.newly_joined_players[player] += 1
            if st.session_state.newly_joined_players[player] >= 2:
                del st.session_state.newly_joined_players[player]
                st.session_state.cooldown_players[player] = 2  # cooldown for 2 full matches

def add_new_players():
    new_names = st.text_input("Add player(s) separated by comma:")
    if st.button("Add Players"):
        names = [n.strip() for n in new_names.split(",") if n.strip()]
        for name in names:
            if name not in st.session_state.players:
                st.session_state.players.append(name)
                st.session_state.match_counts[name] = 0
                st.session_state.last_played_time[name] = datetime.min
                st.session_state.waiting_players.append(name)
                st.session_state.newly_joined_players[name] = 0

def remove_player(name):
    if name in st.session_state.players:
        st.session_state.players.remove(name)
        st.session_state.removed_players[name] = {
            "matches": st.session_state.match_counts.get(name, 0),
            "wins": st.session_state.win_counts.get(name, 0),
        }

# --- UI Layout ---
st.title("🏸 Badminton Match Shuffler")

add_new_players()

if st.button("Start New Match"):
    start_new_match()

if st.session_state.current_match:
    st.subheader("🎮 Current Match")
    team_a, team_b = st.session_state.current_match
    st.markdown(f"🅰️ **Team A**: {', '.join(team_a)}")
    st.markdown(f"🅱️ **Team B**: {', '.join(team_b)}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Team A Wins"):
            submit_match_result("A")
    with col2:
        if st.button("✅ Team B Wins"):
            submit_match_result("B")

st.divider()
st.subheader("📊 Match Stats")
for player in sorted(set(list(st.session_state.match_counts.keys()) + list(st.session_state.removed_players.keys()))):
    matches = st.session_state.match_counts.get(player, 0)
    wins = st.session_state.win_counts.get(player, 0)
    removed = " (❌ Removed)" if player in st.session_state.removed_players else ""
    st.write(f"- {player}{removed}: {matches} matches, {wins} wins")

st.divider()
st.subheader("👥 Players")
for player in st.session_state.players:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(player)
    with col2:
        if st.button(f"Remove {player}", key=f"remove_{player}"):
            remove_player(player)

st.divider()
st.subheader("🕹️ Match History")
for match in reversed(st.session_state.match_history):
    a = ", ".join(match['team_a'])
    b = ", ".join(match['team_b'])
    w = ", ".join(match['winner'])
    st.markdown(f"**Match {match['match']}**: 🅰️ {a} vs 🅱️ {b} → 🏆 **{w}**")
