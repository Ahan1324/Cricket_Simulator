import numpy as np
import pulp

# Parameters
num_teams = 10
num_matches = 70
squad_size = 11
max_transfers = 210
players_per_team = 15

# Simulated expected points (top player: 50, then 45, 40, etc.)
player_points = {t: [50 - 5 * i for i in range(players_per_team)] for t in range(num_teams)}

# Simulated match schedule (each match has two teams)
np.random.seed(42)
match_schedule = [tuple(np.random.choice(num_teams, 2, replace=False)) for _ in range(num_matches)]

# Optimization model
model = pulp.LpProblem("Fantasy_League_Optimization", pulp.LpMaximize)

# Decision variables
x = pulp.LpVariable.dicts("Select", [(p, t) for p in range(players_per_team * num_teams) for t in range(num_matches)], cat="Binary")
y = pulp.LpVariable.dicts("Transfer", [(p, t) for p in range(players_per_team * num_teams) for t in range(num_matches)], cat="Binary")

# Objective: Maximize total fantasy points
model += pulp.lpSum(x[p, t] * player_points[p // players_per_team][p % players_per_team] for p in range(players_per_team * num_teams) for t in range(num_matches))

# Constraints
for t in range(num_matches):
    # Squad size constraint
    model += pulp.lpSum(x[p, t] for p in range(players_per_team * num_teams)) <= squad_size
    
    # Only select players from playing teams
    playing_teams = match_schedule[t]
    model += pulp.lpSum(x[p, t] for p in range(players_per_team * num_teams) if p // players_per_team not in playing_teams) == 0

# Transfer constraints
for p in range(players_per_team * num_teams):
    for t in range(1, num_matches):
        # Transfers occur when a player is selected but wasn't in the previous match
        model += x[p, t] - x[p, t-1] <= y[p, t]

# Total transfer limit
model += pulp.lpSum(y[p, t] for p in range(players_per_team * num_teams) for t in range(num_matches)) <= max_transfers

# Solve the model
model.solve()

# Output selected players and transfers
selected_players = {(p, t): x[p, t].varValue for p in range(players_per_team * num_teams) for t in range(num_matches) if x[p, t].varValue}
transfers_made = {(p, t): y[p, t].varValue for p in range(players_per_team * num_teams) for t in range(num_matches) if y[p, t].varValue}

print("Optimal Player Selections:", selected_players)
print("Transfers Made:", transfers_made)
