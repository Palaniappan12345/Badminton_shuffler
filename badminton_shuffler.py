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

def get_active_players():
    return [p for p in st.session_state.players if p not in st.session_state.removed_players]

def shuffle_match(players):
    random.shuffle(players)
    return players[:2], players[2:4]

def start_new_match():
    all_players = get_active_players()
    if len(all_players) < 4:
        st.session_state.current_match = None
        st.warning("❗ Not enough active players (min 4) to start a match.")
        return

    num_players = len(all_players)

    if num_players in [5, 6]:
        previous_winner = []
        if st.session_state.match_history:
            previous_winner = sorted(st.session_state.match_history[-1]["winner"])

        for _ in range(100):  # attempt to avoid same team winning
            random.shuffle(all_players)
            team_a, team_b = all_players[:2], all_players[2:4]
            current_teams = sorted(team_a), sorted(team_b)
            if sorted(team_a) != previous_winner and sorted(team_b) != previous_winner:
                st.session_state.current_match = (team_a, team_b)
                st.session_state.waiting_players = [p for p in all_players if p not in team_a + team_b]
                return
        st.warning("⚠️ Could not reshuffle to avoid same winning team. Proceeding with random teams.")
        st.session_state.current_match = (all_players[:2], all_players[2:4])
        st.session_state.waiting_players = [p for p in all_players if p not in all_players[:4]]
    else:
        # Use original logic
        if st.session_state.match_history:
            last_match = st.session_state.match_history[-1]
            winner = [p for p in last_match["winner"] if p in all_players]
            loser = [p for p in last_match["loser"] if p in all_players]
            winner_key = tuple(sorted(winner))
            streak = st.session_state.win_streak.get(winner_key, 0)

            if streak < 2 and len(winner) == 2:
                waiting = [p for p in all_players if p not in winner and p not in loser]
                random.shuffle(waiting)
                if len(waiting) < 2:
                    st.session_state.current_match = None
                    st.warning("❗ Not enough waiting players to complete match with winning pair.")
                    return
                next_match = winner + waiting[:2]
            else:
                st.session_state.win_streak[winner_key] = 0
                eligible = [p for p in all_players if p not in winner]
                random.shuffle(eligible)
                if len(eligible) < 4:
                    st.session_state.current_match = None
                    st.warning("❗ Not enough eligible players for next match.")
                    return
                next_match = eligible[:4]
        else:
            next_match = all_players[:4]

        team_a = next_match[:2]
        team_b = next_match[2:4]
        st.session_state.current_match = (team_a, team_b)
        st.session_state.waiting_players = [p for p in all_players if p not in team_a + team_b]

def submit_match_result(winner_team):
    if not st.session_state.current_match:
        return
    team_a, team_b = st.session_state.current_match
    team_a = [p for p in team_a if p not in st.session_state.removed_players]
    team_b = [p for p in team_b if p not in st.session_state.removed_players]

    winner = team_a if winner_team == "A" else team_b
    loser = team_b if winner_team == "A" else team_a

    winner_key = tuple(sorted(winner))
    st.session_state.win_streak[winner_key] = st.session_state.win_streak.get(winner_key, 0) + 1

    for player in team_a + team_b:
        if player not in st.session_state.removed_players:
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
        st.success(f"✅ Added: {', '.join(added)}")
        st.rerun()
    if skipped:
        st.warning(f"⚠️ Already present or removed: {', '.join(skipped)}")

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
            st.session_state.match_counts = defaultdict(int)
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

    # Add Players
    st.markdown("---")
    st.header("➕ Add New Players")
    new_players_input = st.text_input("Enter names (comma-separated)", key="new_players_input")
    if st.button("Add Players"):
        add_new_players(new_players_input)

    # Remove Players
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

    # Waiting Players
    st.markdown("---")
    st.header("🧘 Waiting Players")
    waiting = [p for p in st.session_state.waiting_players if p not in st.session_state.removed_players]
    st.markdown(" ".join([f"`{p}`" for p in waiting]) or "_None_")

    # Removed Players
    st.markdown("---")
    st.header("❌ Removed Players")
    st.markdown(" ".join([f"`{p}`" for p in st.session_state.removed_players]) or "_None_")

    # Match Counts
    st.markdown("---")
    st.header("📊 Matches Played")
    all_players = st.session_state.players + st.session_state.removed_players
    shown = set()
    for p in all_players:
        if p not in shown:
            count = st.session_state.match_counts.get(p, 0)
            status = "🟢 Active" if p not in st.session_state.removed_players else "❌ Removed"
            st.markdown(f"- **{p}**: {count} matches &nbsp;&nbsp;{status}")
            shown.add(p)

    # Match History
    st.markdown("---")
    st.header("📜 Match History")
    if st.session_state.match_history:
        for i, m in enumerate(st.session_state.match_history, 1):
            st.markdown(f"**Match {i}:** {m['team_a']} vs {m['team_b']} → 🏆 **Winner:** {m['winner']}")
    else:
        st.write("_No matches yet._")

    # Reset
    st.markdown("---")
    st.button("🔄 Reset All", on_click=lambda: (reset_all(), st.rerun()))
