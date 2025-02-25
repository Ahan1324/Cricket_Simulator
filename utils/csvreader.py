import csv
from models.player import Player
from models.team import Team
from models.venue import Stadium

def parse_int(value):
    try: 
        return float(value) if value.strip() else 5
    except: 
        return None

def parse_str(value):
    try: 
        return value if value.strip() else None
    except: 
        return None

# Function to read cricketers and return a list of Player objects
def read_cricketers(file_path):
    players = []
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            player = Player(
                name=parse_str(row['name']),
                role=parse_str(row['role']),
                batting_defense=parse_int(row['batting_defense']),
                batting_rotation=parse_int(row['batting_rotation']),
                batting_boundary=parse_int(row['batting_boundary']),
                batting_power=parse_int(row['batting_power']),
                batting_spin=parse_int(row['batting_spin']),
                batting_fast=parse_int(row['batting_fast']),
                batting_swing=parse_int(row['batting_swing']),
                batting_bounce=parse_int(row['batting_bounce']),
                test_ave=parse_int(row['test_ave']),
                odi_ave=parse_int(row['odi_ave']),
                t20_ave=parse_int(row['t20_ave']),
                test_sr=parse_int(row['test_sr']),
                odi_sr=parse_int(row['odi_sr']),
                t20_sr=parse_int(row['t20_sr']),
                bowling_type=parse_str(row['bowling_type']),
                bowling_bounce=parse_int(row['bowling_bounce']),
                bowling_seam=parse_int(row['bowling_seam']),
                bowling_swing=parse_int(row['bowling_swing']),
                bowling_pace=parse_int(row['bowling_pace']),
                bowling_control=parse_int(row['bowling_control']),
                bowling_turn=parse_int(row['bowling_turn']),
                bowling_variations=parse_int(row['bowling_variations']),
                age=parse_int(row['age']),
                fitness=parse_int(row['fitness']),
                fatigue=parse_int(row['fatigue']),
                strain=parse_int(row['strain']),
                form=parse_int(row['form']),
                followers=parse_int(row['followers']),
                marketability=parse_int(row['marketability']),
                injury_status=parse_str(row['injury_status']),
                prevmatch=parse_str(row['prevmatch'])
            )
            players.append(player)
    return players

def read_teams(file_path, players_list):
    teams = []
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            team_name = row['team_name']
            fanbase = parse_int(row['fanbase'])
            player_names = [name.strip() for name in row['player_names'].split(',')]  # Maintain order from file

            # Ensure players are selected in the order they appear in player_names
            player_dict = {p.name.strip(): p for p in players_list}
            team_players = [player_dict[name] for name in player_names if name in player_dict]

            if not team_players:
                print(f"Warning: No players found for team {team_name}")

            teams.append(Team(team_name, team_players, fanbase))
    return teams

# Function to read grounds and return a list of Ground objects
def read_grounds(file_path):
    grounds = []
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            ground = Stadium(
                id=parse_int(row['id']),
                name=parse_str(row['ground_name']),
                quality=parse_int(row['quality']),
                capacity=parse_int(row['capacity']),
                pace=parse_int(row['pace']),
                turn=parse_int(row['turn']),
                bounce=parse_int(row['bounce']),
                hardness=parse_int(row['hardness']),
                grass_cover=parse_int(row['grass_cover'])
            )
            grounds.append(ground)
    return grounds
