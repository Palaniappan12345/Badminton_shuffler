import streamlit as st
import random
from collections import defaultdict

st.set_page_config(page_title="🏈 Badminton Match Shuffler", layout="centered")

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
if "newly_joined_players" not in st.session_state:
    st.session_state.newly_joined_players = defaultdict(int)
if "cooldown_players" not in st.session_state:
    st.session_state.cooldown_players = defaultdict(int)
if "removed_players" not in st.session_state:
    st.session_state.removed_players = []
if "player_names_input" not in st.session_state:
    st.session_state.player_names_input = {}

# --- Core Functions ---
def reset_all():
    for key in list(st.session_state.keys()):
        del st.session_state[key]

def get_active_players():
    return [p for p in st.session_state.players if p not in st.session_state.removed_players]

def pick_fair_four():
    active = get_active_players()
    eligible_players = [p for p in active if p not in st.session_state.cooldown_players or st.session_state.cooldown_players[p] <= 0]
    sorted_players = sorted(eligible_players, key=lambda p: (st.session_state.match_counts[p], st.session_state.last_played_time[p]))
    return sorted_players[:4]

def start_new_match():
    all_players = get_active_players()

    # Decrease cooldown counters
    to_remove = []
    for p in st.session_state.cooldown_players:
        st.session_state.cooldown_players[p] -= 1
        if st.session_state.cooldown_players[p] <= 0:
            to_remove.append(p)
    for p in to_remove:
        del st.session_state.cooldown_players[p]

    if len(all_players) < 4:
        st.session_state.current_match = []
        return

    if len(st.session_state.match_history) == 0:
        selected = random.sample(all_players, 4)
    elif len(all_players) in [5, 6]:
        selected = pick_fair_four()
    else:
        last_match = st.session_state.match_history[-1]
        winner = [p for p in last_match["winner"] if p in all_players]
        loser = [p for p in last_match["loser"] if p in all_players]

        waiting = [p for p in all_players if p not in winner + loser and p not in st.session_state.cooldown_players]

        if len(waiting) >= 2:
            new_players = random.sample(waiting, 2)
            eligible = [p for p in all_players if p not in winner and p not in st.session_state.cooldown_players]
            if len(eligible) >= 2:
                others = random.sample(eligible, 2)
                selected = new_players + others
            else:
                selected = random.sample(all_players, 4)
        else:
            eligible = [p for p in all_players if p not in winner and p not in st.session_state.cooldown_players]
            if len(eligible) >= 4:
                selected = random.sample(eligible, 4)
            else:
                selected = random.sample([p for p in all_players if p not in st.session_state.cooldown_players], 4)

    random.shuffle(selected)
    st.session_state.current_match = [selected[:2], selected[2:]]

def submit_match_result(winner_team):
    match = st.session_state.current_match
    team_a, team_b = match
    winner = team_a if winner_team == "A" else team_b
    loser = team_b if winner_team == "A" else team_a

    for p in team_a + team_b:
        st.session_state.match_counts[p] += 1
        st.session_state.last_played_time[p] = len(st.session_state.match_history)

    for player in winner:
        st.session_state.win_counts[player] += 1

    for player in team_a + team_b:
        if player in st.session_state.newly_joined_players:
            st.session_state.newly_joined_players[player] += 1
            if st.session_state.newly_joined_players[player] >= 2:
                del st.session_state.newly_joined_players[player]
                st.session_state.cooldown_players[player] = 2

    st.session_state.match_history.append({
        "team_a": team_a,
        "team_b": team_b,
        "winner": winner,
        "loser": loser
    })

    st.session_state.waiting_players = [p for p in get_active_players() if p not in team_a + team_b]
    start_new_match()


def add_new_players(names_input):
    new_names = [name.strip() for name in names_input.split(",") if name.strip()]
    existing = set(st.session_state.players)
    added = []
    for name in new_names:
        if name not in existing:
            st.session_state.players.append(name)
            st.session_state.waiting_players.append(name)
            st.session_state.newly_joined_players[name] = 0
            added.append(name)
    if added:
        st.success(f"Added new players: {', '.join(added)}")
        start_new_match()
        st.rerun()

# --- UI ---
st.title("🏈 Badminton Match Shuffler")

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
            st.session_state.match_counts = defaultdict(int)
            st.session_state.win_counts = defaultdict(int)
            st.session_state.last_played_time = defaultdict(lambda: -1)
            st.session_state.newly_joined_players = defaultdict(int)
            st.session_state.cooldown_players = defaultdict(int)
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
    waiting = [p for p in st.session_state.waiting_players if p not in st.session_state.removed_players]
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
