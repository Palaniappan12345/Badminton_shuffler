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
    st.session_state.current_match = None
if "win_streak" not in st.session_state:
    st.session_state.win_streak = {}
if "last_losers" not in st.session_state:
    st.session_state.last_losers = []
if "match_counts" not in st.session_state:
    st.session_state.match_counts = defaultdict(int)
if "player_count" not in st.session_state:
    st.session_state.player_count = 4
if "player_names_input" not in st.session_state:
    st.session_state.player_names_input = {}
if "removed_players" not in st.session_state:
    st.session_state.removed_players = []

# --- Logic Functions ---
def reset_all():
    st.session_state.players = []
    st.session_state.waiting_players = []
    st.session_state.match_history = []
    st.session_state.current_match = None
    st.session_state.win_streak = {}
    st.session_state.last_losers = []
    st.session_state.match_counts = defaultdict(int)
    st.session_state.player_names_input = {}
    st.session_state.removed_players = []

def start_new_match():
    all_players = st.session_state.players.copy()
    if st.session_state.match_history:
        last_match = st.session_state.match_history[-1]
        winner = last_match["winner"]
        loser = last_match["loser"]
        winner_key = tuple(sorted(winner))
        streak = st.session_state.win_streak.get(winner_key, 0)

        if streak < 2:
            waiting = [p for p in st.session_state.waiting_players if p not in winner and p not in loser]
            random.shuffle(waiting)
            if len(waiting) < 2:
                st.warning("Not enough players to form new match with current rules.")
                st.session_state.current_match = None
                return
            next_match = winner + waiting[:2]
        else:
            st.session_state.win_streak[winner_key] = 0
            eligible = [p for p in all_players if p not in winner]
            random.shuffle(eligible)
            if len(eligible) < 4:
                st.warning("Not enough players to start new match.")
                st.session_state.current_match = None
                return
            next_match = eligible[:4]
    else:
        # First match: use the first 4 players as entered
        next_match = st.session_state.players[:4]

    team_a = next_match[:2]
    team_b = next_match[2:4]
    st.session_state.current_match = (team_a, team_b)
    st.session_state.waiting_players = [p for p in all_players if p not in team_a + team_b]

def submit_match_result(winner_team):
    if not st.session_state.current_match:
        return
    team_a, team_b = st.session_state.current_match
    winner = team_a if winner_team == "A" else team_b
    loser = team_b if winner_team == "A" else team_a

    winner_key = tuple(sorted(winner))
    st.session_state.win_streak[winner_key] = st.session_state.win_streak.get(winner_key, 0) + 1

    for player in team_a + team_b:
        st.session_state.match_counts[player] += 1

    st.session_state.match_history.append({
        "team_a": team_a,
        "team_b": team_b,
        "winner": winner,
        "loser": loser
    })
    st.session_state.waiting_players += loser
    st.session_state.last_losers = loser
    st.session_state.current_match = None

    start_new_match()

def add_new_players(names_input):
    names = [name.strip() for name in names_input.split(",") if name.strip()]
    added = []
    skipped = []
    for name in names:
        if name not in st.session_state.players and name not in st.session_state.removed_players:
            st.session_state.players.append(name)
            st.session_state.waiting_players.append(name)
            added.append(name)
        else:
            skipped.append(name)

    if added:
        st.success(f"✅ Added new players: {', '.join(added)}")
        st.rerun()
    if skipped:
        st.warning(f"⚠️ These players were already in the game or removed: {', '.join(skipped)}")

# --- UI Starts Here ---
st.title("🏸 Badminton Match Shuffler")

if not st.session_state.players:
    st.header("👥 Add Players")
    st.session_state.player_count = st.slider("Select number of players", 4, 9, value=4)

    names = []
    for i in range(1, st.session_state.player_count + 1):
        name = st.text_input(f"Player {i} Name", key=f"player_{i}")
        st.session_state.player_names_input[f"player_{i}"] = name
        names.append(name)

    if st.button("✅ Start Match"):
        player_list = [name.strip() for name in names if name.strip()]
        if len(player_list) != len(set(player_list)):
            st.error("⚠️ Duplicate names found! Please use unique names for each player.")
        elif len(player_list) < 4:
            st.warning("Please enter at least 4 valid player names.")
        else:
            st.session_state.players = player_list
            st.session_state.waiting_players = player_list.copy()
            st.session_state.match_counts = defaultdict(int)
            start_new_match()
            st.rerun()
else:
    st.header("🎮 Current Match")
    if st.session_state.current_match:
        team_a, team_b = st.session_state.current_match
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🅰️ Team A")
            st.success(", ".join(team_a))
        with col2:
            st.markdown("### 🅱️ Team B")
            st.info(", ".join(team_b))

        winner_choice = st.radio("🏆 Who won this match?", ["A", "B"], horizontal=True)
        if st.button("Submit Result"):
            submit_match_result(winner_choice)
            st.rerun()
    else:
        st.info("⚠️ No active match. Waiting for result or new match.")

    # --- Add New Players Section ---
    st.markdown("---")
    st.header("➕ Add New Players")
    new_players_input = st.text_input("Enter new player names (comma-separated)", key="new_players_input")
    if st.button("Add Players"):
        add_new_players(new_players_input)

    # --- Remove Players Section ---
    st.markdown("---")
    st.header("❌ Remove Players")

    removable_players = [p for p in st.session_state.players]
    players_to_remove = st.multiselect("Select players to remove", removable_players, key="remove_players")

    if st.button("Remove Selected Players"):
        if players_to_remove:
            for p in players_to_remove:
                if p in st.session_state.players:
                    st.session_state.players.remove(p)
                if p in st.session_state.waiting_players:
                    st.session_state.waiting_players.remove(p)
                if p not in st.session_state.removed_players:
                    st.session_state.removed_players.append(p)
            st.success(f"✅ Removed: {', '.join(players_to_remove)}")
            st.rerun()
        else:
            st.warning("⚠️ No players selected.")

    # --- Waiting Players ---
    st.markdown("---")
    st.header("🧘 Waiting Players")
    st.markdown(" ".join([f"`{p}`" for p in st.session_state.waiting_players]) or "_None_")

    # --- Removed Players ---
    st.markdown("---")
    st.header("❌ Removed Players")
    if st.session_state.removed_players:
        st.markdown(" ".join([f"`{p}`" for p in st.session_state.removed_players]))
    else:
        st.write("_None_")

    # --- Match Counts ---
    st.markdown("---")
    st.header("📊 Matches Played")
    match_counts = st.session_state.match_counts
    if match_counts:
        for player in st.session_state.players:
            st.markdown(f"- **{player}**: {match_counts[player]} match{'es' if match_counts[player] != 1 else ''}")
    else:
        st.write("No matches recorded yet.")

    # --- Match History ---
    st.markdown("---")
    st.header("📜 Match History")
    if st.session_state.match_history:
        for i, match in enumerate(st.session_state.match_history, 1):
            st.markdown(
                f"**Match {i}:** {match['team_a']} vs {match['team_b']} → 🏆 **Winner:** {match['winner']} "
            )
    else:
        st.write("_No matches yet._")

    st.markdown("---")
    st.button("🔄 Reset All", on_click=lambda: (reset_all(), st.rerun()))
