import functools
from collections import defaultdict

# -----------------------------
# SETUP: Define teams and schedule
# -----------------------------
teams = [
    "KKR", "RCB", "SRH", "DC", "PBKS", "CSK", "MI", "RR", "GT", "LSG"
]

team_to_index = {team: i for i, team in enumerate(teams)}
T = len(teams)

schedule = [
    ("Sat, 22 Mar '25", "KKR", "RCB", "Eden Gardens", "7:30 pm Local"),
    ("Sun, 23 Mar '25", "SRH", "RR", "Hyderabad", "3:30 pm Local"),
    ("Sun, 23 Mar '25", "CSK", "MI", "Chennai", "7:30 pm Local"),
    ("Mon, 24 Mar '25", "DC", "LSG", "Visakhapatnam", "7:30 pm Local"),
    ("Tue, 25 Mar '25", "GT", "PBKS", "Ahmedabad", "7:30 pm Local"),
    ("Wed, 26 Mar '25", "RR", "KKR", "Guwahati", "7:30 pm Local"),
    ("Thu, 27 Mar '25", "SRH", "LSG", "Hyderabad", "7:30 pm Local"),
    ("Fri, 28 Mar '25", "CSK", "RCB", "Chennai", "7:30 pm Local"),
    ("Sat, 29 Mar '25", "GT", "MI", "Ahmedabad", "7:30 pm Local"),
    ("Sun, 30 Mar '25", "DC", "SRH", "Visakhapatnam", "3:30 pm Local"),
    ("Sun, 30 Mar '25", "RR", "CSK", "Guwahati", "7:30 pm Local"),
    ("Mon, 31 Mar '25", "MI", "KKR", "Wankhede", "7:30 pm Local"),
    ("Tue, 01 Apr '25", "LSG", "PBKS", "Lucknow", "7:30 pm Local"),
    ("Wed, 02 Apr '25", "RCB", "GT", "Bengaluru", "7:30 pm Local"),
    ("Thu, 03 Apr '25", "KKR", "SRH", "Eden Gardens", "7:30 pm Local"),
    ("Fri, 04 Apr '25", "LSG", "MI", "Lucknow", "7:30 pm Local"),
    ("Sat, 05 Apr '25", "CSK", "DC", "Chennai", "3:30 pm Local"),
    ("Sat, 05 Apr '25", "PBKS", "RR", "Mullanpur", "7:30 pm Local"),
    ("Sun, 06 Apr '25", "KKR", "LSG", "Eden Gardens", "3:30 pm Local"),
    ("Sun, 06 Apr '25", "SRH", "GT", "Hyderabad", "7:30 pm Local"),
    ("Mon, 07 Apr '25", "MI", "RCB", "Wankhede", "7:30 pm Local"),
    ("Tue, 08 Apr '25", "PBKS", "CSK", "Mullanpur", "7:30 pm Local"),
    ("Wed, 09 Apr '25", "GT", "RR", "Ahmedabad", "7:30 pm Local"),
    ("Thu, 10 Apr '25", "RCB", "DC", "Bengaluru", "7:30 pm Local"),
    ("Fri, 11 Apr '25", "CSK", "KKR", "Chennai", "7:30 pm Local"),
    ("Sat, 12 Apr '25", "LSG", "GT", "Lucknow", "3:30 pm Local"),
    ("Sat, 12 Apr '25", "SRH", "PBKS", "Hyderabad", "7:30 pm Local"),
    ("Sun, 13 Apr '25", "RR", "RCB", "Jaipur", "3:30 pm Local"),
    ("Sun, 13 Apr '25", "DC", "MI", "Delhi", "7:30 pm Local"),
    ("Mon, 14 Apr '25", "LSG", "CSK", "Lucknow", "7:30 pm Local"),
    ("Tue, 15 Apr '25", "PBKS", "KKR", "Mullanpur", "7:30 pm Local"),
    ("Wed, 16 Apr '25", "DC", "RR", "Delhi", "7:30 pm Local"),
    ("Thu, 17 Apr '25", "MI", "SRH", "Wankhede", "7:30 pm Local"),
    ("Fri, 18 Apr '25", "RCB", "PBKS", "Bengaluru", "7:30 pm Local"),
    ("Sat, 19 Apr '25", "GT", "DC", "Ahmedabad", "3:30 pm Local"),
    ("Sat, 19 Apr '25", "RR", "LSG", "Jaipur", "7:30 pm Local"),
    ("Sun, 20 Apr '25", "PBKS", "MI", "Mullanpur", "3:30 pm Local"),
    ("Sun, 20 Apr '25", "CSK", "GT", "Chennai", "7:30 pm Local"),
]

N_matches = len(schedule)

# -----------------------------
# Helper: state representation
# -----------------------------
initial_state = [0] * T
initial_state[0] = 11
initial_state = tuple(initial_state)

# -----------------------------
# Allowed transitions: neighbors(state)
# -----------------------------
@functools.lru_cache(maxsize=None)
def neighbors(state):
    state = list(state)
    result = set()
    result.add(tuple(state))

    def gen_swaps(curr_state, swaps_left):
        if swaps_left == 0:
            return
        for i in range(T):
            if curr_state[i] > 0:
                for j in range(T):
                    if i == j:
                        continue
                    new_state = curr_state.copy()
                    new_state[i] -= 1
                    new_state[j] += 1
                    new_tuple = tuple(new_state)
                    if new_tuple not in result:
                        result.add(new_tuple)
                        gen_swaps(new_state, swaps_left - 1)

    gen_swaps(state, 3)
    return result

# -----------------------------
# Dynamic Programming: dp(match_index, state)
# -----------------------------
@functools.lru_cache(maxsize=None)
def dp(match_index, state):
    if match_index == N_matches:
        return 0, None

    date, team_a, team_b, venue, time = schedule[match_index]
    idx_a = team_to_index[team_a]
    idx_b = team_to_index[team_b]
    reward_here = state[idx_a] + state[idx_b]

    best_total = -1
    best_next_state = None

    for next_state in neighbors(state):
        future_reward, _ = dp(match_index + 1, next_state)
        total_reward = reward_here + future_reward
        if total_reward > best_total:
            best_total = total_reward
            best_next_state = next_state

    return best_total, best_next_state

# -----------------------------
# Reconstruct the optimal policy
# -----------------------------
def reconstruct_policy():
    policy = {}
    state = initial_state
    total = 0

    for i in range(N_matches):
        date, team_a, team_b, venue, time = schedule[i]
        idx_a = team_to_index[team_a]
        idx_b = team_to_index[team_b]
        reward_here = state[idx_a] + state[idx_b]
        total += reward_here

        _, next_state = dp(i, state)

        changes = []
        if next_state is not None:
            for idx in range(T):
                if state[idx] != next_state[idx]:
                    changes.append((teams[idx], state[idx], next_state[idx]))

        policy[i] = {
            'match': i + 1,
            'match_pair': schedule[i],
            'state_before': state,
            'reward': reward_here,
            'state_after': next_state,
            'changes': changes
        }

        state = next_state

    return total, policy

# -----------------------------
# Run the dynamic programming and get the optimal policy.
# -----------------------------

optimal_total, optimal_policy = reconstruct_policy()

print("Optimal total appearances over the season:", optimal_total)
print("Transfer policy per match:")
for i in range(N_matches):
    entry = optimal_policy[i]
    date, team_a, team_b, venue, time = entry['match_pair']
    print(f"Match {entry['match']:2d} {team_a} vs {team_b} - Reward: {entry['reward']}, Transfers: {entry['changes']}")