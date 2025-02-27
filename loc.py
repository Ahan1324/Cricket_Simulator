import discord
from discord.ext import commands
from utils.csvreader import read_cricketers, read_teams, read_grounds
from models.player import Player
from models.team import Team
from models.venue import Stadium
import math
import asyncio
import time
import random
from commentary import *

import numpy as np
from scipy.optimize import minimize

# Load data from CSV files
players = read_cricketers('data/players.csv')
teams = read_teams('data/teams.csv', players)
grounds = read_grounds('data/venues.csv')


#  up the bot with a command prefix
# Create an instance of Intents
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent

# Initialize the bot with the intents
bot = commands.Bot(command_prefix="!", intents=intents)

import math

def calculate_revenue(format, fanbase_team1, fanbase_team2, player_followers, tournament_profile, closeness, runs_scored, stadium_quality, stadium_capacity):
    """
    Calculate cricket match revenue split by ticket sales and broadcast rights.
    
    Args:
        format (str): Match format ('T20', 'ODI', 'Test').
        fanbase_team1 (int): Fanbase of team 1 in millions.
        fanbase_team2 (int): Fanbase of team 2 in millions.
        player_followers (list): Instagram followers of each player in millions.
        tournament_profile (int): Tournament importance (1 to 5).
        closeness (float): Match competitiveness (0 to 1).
        runs_scored (int): Total runs scored.
        stadium_quality (int): Stadium quality rating (1 to 10).
        stadium_capacity (int): Stadium capacity (number of seats).
    
    Returns:
        tuple: (broadcast_revenue, ticket_revenue) in dollars.
    """
    # Define format multipliers
    format_multipliers = {'T20': 1.2, 'ODI': 1.0, 'Test': 0.8}
    if format not in format_multipliers:
        raise ValueError("Invalid format. Use 'T20', 'ODI', or 'Test'.")
    
    # Calculate total fanbases
    team_fanbase = fanbase_team1 + fanbase_team2
    player_fanbase = player_followers
    
    # Calculate attractiveness score
    A = (team_fanbase / 100) * (player_fanbase / 50)**0.5 * tournament_profile * \
        format_multipliers[format] * (closeness / 0.5)**0.5 * (runs_scored / 300)**0.2 * \
        (stadium_quality / 5)**0.3
    
    # Calculate broadcast revenue
    broadcast_revenue = 10_000_0 * A
    
    # Calculate ticket revenue
    occupancy_rate = 1 - math.exp(-1.609 * A)
    ticket_revenue = stadium_capacity * 25 * occupancy_rate
    
    return broadcast_revenue, ticket_revenue

       
def display_scorecard(batting_stats, bowling_stats, team_name, score, wickets, detailed_overs):
    """Display the scorecard for a team with enhanced details."""

    overs_completed = len(detailed_overs) // 6
    balls_in_current_over = len(detailed_overs) % 6
    current_over = f"{overs_completed}.{balls_in_current_over}"
    message = ""
    message += (f"{team_name} {score}/{wickets} ({current_over})")
    
    message += ("\nBatting:\n")
    message += ("Batter           Runs  Balls  SR\n")
    message += ("-" * 35)
    for player, stats in batting_stats.items():
        if stats['balls'] > 0:  # Only show batsmen who faced deliveries
            strike_rate = (stats['runs'] * 100) / stats['balls']
            status = "*" if not stats['out'] else ""
            message += (f"{player:<15} {stats['runs']}{status:<5} {stats['balls']:<6} {strike_rate:>5.1f}\n")

    message += ("\nBowling:\n")
    message += ("Bowler           O    R    W    Econ\n")
    message += ("-" * 40)
    for player, stats in bowling_stats.items():
        if stats['overs'] > 0:  # Only show bowlers who bowled
            economy = stats['runs'] / stats['overs'] if stats['overs'] > 0 else 0
            message += (f"{player:<15} {stats['overs']:<4} {stats['runs']:<4} {stats['wickets']:<4} {economy:>5.1f}\n")


    print(message)

    if False:
        print(f"\nBall by Ball with Overs for {team_name}:")
        
        current_score = 0
        current_wickets = 0
        
        # Initialize batsmen
        batsmen = list(batting_stats.keys())
        striker = batsmen[0]
        non_striker = batsmen[1]
        batsmen_scores = {name: {'runs': 0, 'balls': 0} for name in batting_stats}
        
        # Initialize bowling_stats for all bowlers to zero
        bowlers = set(ball.split()[0] for ball in detailed_overs)
        for bowler in bowlers:
            bowling_stats[bowler] = {'overs': 0, 'runs': 0, 'wickets': 0}
        
        # Process balls over by over
        total_balls = len(detailed_overs)
        for i in range(0, total_balls, 6):
            over_num = i // 6
            over_balls = detailed_overs[i:min(i+6, total_balls)]
            bowler = over_balls[0].split()[0]
            
            print(f"\nOver {over_num + 1}:")
            over_runs = 0
            over_wickets = 0
            
            # Process each ball in the over
            for ball_num, ball in enumerate(over_balls, 1):
                print(f"  {over_num}.{ball_num}: {ball}")
                
                if "OUT" in ball:
                    over_wickets += 1
                    current_wickets += 1
                    batsmen_scores[striker]['balls'] += 1
                    if current_wickets < len(batsmen) - 1:
                        striker = batsmen[current_wickets + 1]
                else:
                    runs = int(ball.split()[-2])
                    over_runs += runs
                    current_score += runs
                    batsmen_scores[striker]['runs'] += runs
                    batsmen_scores[striker]['balls'] += 1
                    if runs % 2 == 1:
                        striker, non_striker = non_striker, striker
            
            # Rotate strike at end of over
            striker, non_striker = non_striker, striker
            
            # Update bowling figures
            bowling_stats[bowler]['overs'] += 1
            bowling_stats[bowler]['runs'] += over_runs
            bowling_stats[bowler]['wickets'] += over_wickets
            
            # Print single-line summary after each over
            striker_stats = f"{striker}: {batsmen_scores[striker]['runs']}*({batsmen_scores[striker]['balls']})"
            non_striker_stats = f"{non_striker}: {batsmen_scores[non_striker]['runs']}({batsmen_scores[non_striker]['balls']})"
            bowler_stats = f"{bowler}: {over_runs}/{over_wickets} ({bowling_stats[bowler]['overs']}--{bowling_stats[bowler]['runs']}-{bowling_stats[bowler]['wickets']})"
            
            print(f"Score: {current_score}/{current_wickets} | {striker_stats}, {non_striker_stats} | {bowler_stats}")
        
    


def display_scorecard_discord(team_name, batting_stats, bowling_stats):
    """Display formatted batting and bowling scorecards"""
    # Create batting scorecard
    batting_card = f"**{team_name} Batting**\n```\n"
    batting_card += "Batter          Runs  Balls  SR\n"
    batting_card += "-" * 35 + "\n"
    
    for player, stats in batting_stats.items():
        strike_rate = (stats["runs"] / stats["balls"] * 100) if stats["balls"] > 0 else 0
        not_out = "" if stats["out"] else "*"
        batting_card += f"{player:<15} {stats['runs']:<5}{not_out} {stats['balls']:<6} {strike_rate:.2f}\n"
    
    batting_card += "```"
    print(batting_card)

    # Create bowling scorecard
    bowling_card = f"**{team_name} Bowling**\n```\n"
    bowling_card += "Bowler          O    M    R    W    Econ\n"
    bowling_card += "-" * 45 + "\n"
    
    for player, stats in bowling_stats.items():
        if stats["overs"] > 0:  # Only show bowlers who bowled
            economy = stats["runs"] / stats["overs"] if stats["overs"] > 0 else 0
            bowling_card += f"{player:<15} {stats['overs']:<4}  {stats['runs']:<4} {stats['wickets']:<4} {economy:.2f}\n"
    
    bowling_card += "```"
    print(bowling_card)



def play_match(team1name: str, team2name: str, venuename: str, format: str):
    """
    Command to start a match simulation.
    Loads teams, venue, and match format, then calls the match simulation logic.
    """
    print(f"Match Between {team1name} & {team2name}")
    players = read_cricketers("data/players.csv")
    grounds = read_grounds("data/venues.csv")
    teams = read_teams("data/teams.csv", players)
    teams = read_teams('data/teams.csv', players)
    print(f"Loaded teams: {[team.name for team in teams]}")
    print(f"Loaded grounds: {[ground.name for ground in grounds]}")
    # Find the requested teams
    team1 = next((team for team in teams if team.name.lower() == team1name.lower()), None)
    team2 = next((team for team in teams if team.name.lower() == team2name.lower()), None)
    
    # Find the requested ground
    ground = next((g for g in grounds if g.name.lower() == venuename.lower()), None)

    # Valnameate inputs
    if not team1:
        print(f"Team '{team1name}' not found!")
        return
    if not team2:
        print(f"Team '{team2name}' not found!")
        return
    if not ground:
        print(f"Ground '{venuename}' not found!")
        return
    if format.lower() not in ["test", "odi", "t20"]:
        print("Invalname match format! Choose from: Test, ODI, T20.")
        return

    # Confirm match setup
    print(f"Starting {format.upper()} match between {team1.name} and {team2.name} at {ground.name}!")

    for player in team1.players: 
        player.set_match_fitness()
    for player in team2.players: 
        player.set_match_fitness()

    # Placeholder for match simulation logic
    # TODO: Implement the match simulation logic
    print(team1.players)
    print(team2.players)
    assert len(team1.players) == 11
    assert len(team2.players) == 11
    if format.upper() == "ODI": 
        return simulate_odi(team1, team2, ground)
    if format.lower() == "test":
        return simulate_test(team1,team2, ground)
    if format.upper() == "T20":
        return simulate_t20(team1,team2, ground)

    

def calculate_aggression_t20(over, pitch, target, striker, non_striker, settled_striker, settled_non_striker, wickets_in_hand, score):
    """
    Determines the appropriate aggression level for a T20 innings continuously.

    Parameters:
    - over (float): The current over number (0 to 19.5).
    - pitch (dict): Pitch conditions (pace, turn, bounce, grass_cover) - not used here.
    - target (int or None): Target score (None if batting first).
    - striker (object): Striker with attributes like odi_ave, odi_sr - not used here.
    - non_striker (object): Non-striker with attributes like odi_ave, odi_sr - not used here.
    - settled_striker (float): Striker's settled meter (0 to 100).
    - settled_non_striker (float): Non-striker's settled meter (0 to 100).
    - wickets_in_hand (int): Number of wickets remaining (1 to 10).

    Returns:
    - float: Recommended aggression level (0.5 to 2.0+), per provided data.
    """
    base_rpo = 9  # Standard T20 base RPO

    # Phase-based adjustment
    if over < 6:
        base_rpo += -1 + math.log(over + 1, 2.7)      # Powerplay: aggressive start
    elif over < 15:
        base_rpo += 1.4 * 3.5 ** ((over - 15) / 25)  # Middle overs: steady increase
    else:
        base_rpo += ((over - 15))**1.2            # Death overs: ramp up to ~14 RPO by over 19

    # Settled striker adjustment (assuming 0-100 scale)
    if settled_striker < 30:
        base_rpo -= (40 - settled_striker) / 10

    # Wicket adjustment
    wickets_lost = 10 - wickets_in_hand
    if over > 6:
        base_rpo -= wickets_lost * 1.5  # Less harsh penalty
    else:
        base_rpo += (wickets_in_hand - 7 + over / 5)  # Encourage aggression early

    # Target chasing adjustment
    if target is not None:
        rpo_needed = (target-score)/ (20 - over)  # Approximate required RPO
        target_factor = 1 + (1 / (1 + math.exp(-0.5 * (rpo_needed - base_rpo))))
        base_rpo *= target_factor


    if over > 15:  
        base_rpo += (over-15) ** 0.4
    # Convert to aggression level
    aggression = base_rpo / 7.5
    minbyphase = 3
    if over < 6: 
        minbyphase = 1.8
    if over < 15:
        minbyphase = 2
    else: 
        base_rpo += wickets_in_hand - 4

    
    return min(max(0.5, aggression),minbyphase)  # Align with data’s minimum

def calculate_aggression_odi(over, pitch, target, striker, non_striker, settled_striker, settled_non_striker,wickets_in_hand, score):
    """
    Determines the appropriate aggression level (target RPO) for an ODI innings continuously.

    Parameters:
    - over (int): The current over number.
    - pitch (dict): A dictionary containing pitch conditions (pace, turn, bounce, grass_cover).
    - target (int or None): The target score (None if batting first).
    - striker (player object): The striker with attributes like odi_ave and odi_sr.
    - non_striker (player object): The non-striker with attributes like odi_ave and odi_sr.
    - settled_striker (float): The settled meter value of the striker (0 to 10).
    - settled_non_striker (float): The settled meter value of the non-striker (0 to 10).

    Returns:
    - float: The recommended aggression level as target_rpo.
    """
    # Step 1: Calculate base RPO based on over (baseline)
    base_rpo = 4  # Standard ODI base RPO
    if over < 10:
        base_rpo += 2 * math.log(over + 1, 2.7)  # Powerplay: aggressive start
    elif over < 35:
        base_rpo += 1 * 2.7 ** ((over - 10) / 25)  # Middle overs: steady increase
    elif over < 45:
        base_rpo += 2 * (over - 35) / 100 + 2.7 ** ((over - 35) / 8)  # Death overs: sharp rise
    else: 
        base_rpo = + over - 30


    # Step 3: Target chasing adjustment
    if target is not None and over < 50:
        rpo_needed = (target-score) / (50 - over)
        target_factor = 1 + (1 / (1 + math.exp(-0.5 * (rpo_needed - base_rpo)))) - 0.5
        base_rpo *= target_factor

    if over < 40: 
        if settled_striker < 30:
            base_rpo -= (30-settled_striker)/10
    
    wickets_lost = 10-wickets_in_hand
    if over > 10: 
        base_rpo -= wickets_lost
    elif over > 25: 
        base_rpo += (wickets_in_hand-9+over/10) 
    else: 
        base_rpo += (wickets_in_hand * 5 - (50 -over))/5




    return max(0.5,base_rpo/5)


def simulate_test(team1, team2, venue):
    """Simulate a Test match between two teams, including follow-ons."""

    # Random toss to decide who bats first
    if random.randint(1, 100) > 100:
        team1, team2 = team2, team1

    pitch = venue

    # Simulate first innings of team1
    team1_score1, team1_wickets1, team1_batting_stats1, team1_bowling_stats1 = simulate_test_innings(team1, team2, pitch)

    # Display scorecard for team 1 (first innings)
    display_scorecard(team1_batting_stats1, team1_bowling_stats1, team1.name, team1_score1, team1_wickets1, "1st Innings")

    # Simulate first innings of team2
    team2_score1, team2_wickets1, team2_batting_stats1, team2_bowling_stats1 = simulate_test_innings(team2, team1, pitch)

    # Display scorecard for team 2 (first innings)
    display_scorecard(team2_batting_stats1, team2_bowling_stats1, team2.name, team2_score1, team2_wickets1, "1st Innings")

    # Follow-on logic
    if team1_score1 - team2_score1 >= 200:
        print(f"{team1.name} enforces the follow-on on {team2.name}!")
        # Team2 bats their second innings (follow-on)
        team2_score2, team2_wickets2, team2_batting_stats2, team2_bowling_stats2 = simulate_test_innings(team2, team1, pitch)
        display_scorecard_discord(team2.name, team2_batting_stats2, team2_bowling_stats2)

        # Team1 bats in their second innings, chasing a target:
        # Target = (team2 first + team2 second) - team1 first + 1
        target = team2_score1 + team2_score2 - team1_score1 + 1
        print(f"{team1.name} needs {target} runs to win in the final innings!")
        team1_score2, team1_wickets2, team1_batting_stats2, team1_bowling_stats2 = simulate_test_innings(team1, team2, pitch, target=target)
        display_scorecard_discord(team1.name, team1_batting_stats2, team1_bowling_stats2)

        # Decide result based on the final innings
        if team1_score2 >= target:
            wickets_remaining = 10 - team1_wickets2
            print(f"{team1.name} wins by {wickets_remaining} wickets!")
            return{team1.name}
        else:
            runs_short = target - team1_score2
            print(f"{team2.name} wins by {runs_short} runs!")
            return{team2.name}
    else:
        # No follow-on: team1 bats their second innings
        team1_score2, team1_wickets2, team1_batting_stats2, team1_bowling_stats2 =  simulate_test_innings(team1, team2, pitch)
        display_scorecard_discord(team1.name, team1_batting_stats2, team1_bowling_stats2)

        # Team2 chases in their second innings:
        # Target = (team1 first + team1 second) - team2 first + 1
        target = team1_score1 + team1_score2 - team2_score1 + 1
        if target < 0: 
            print(f"{team2.name} wins by an innings and {-target} runs")
            return team2.name
        print(f"{team2.name} needs {target} runs to win in the final innings!")
        team2_score2, team2_wickets2, team2_batting_stats2, team2_bowling_stats2 = simulate_test_innings(team2, team1, pitch, target=target)
        display_scorecard_discord(team2.name, team2_batting_stats2, team2_bowling_stats2)

        # Decide result based on the final innings
        if team2_score2 >= target:
            wickets_remaining = 10 - team2_wickets2
            print(f"{team2.name} wins by {wickets_remaining} wickets!")
            return team2.name
        else:
            runs_short = target - team2_score2
            print(f"{team1.name} wins by {runs_short} runs!")
            return team1.name




def get_ball_probabilities_test(expected_runs):
    """
    Calculates a distribution of weights for runs (0, 1, 2, 3, 4, 6) 
    that result in the given expected runs, based on a scaled distribution.

    Args:
        expected_runs (float): The target expected runs.
        striker (bool): A boolean representing whether the batter is a striker (not used in this simplified version).

    Returns:
        numpy.ndarray: An array of probabilities for runs (0, 1, 2, 3, 4, 6).
    """

    runs = np.array([0, 1, 2, 3, 4, 6])
    base_probs = np.array([0.8, 0.12, 0.02, 0.01, 0.04, 0.01])

    def calculate_expected(probs):
        return np.sum(runs * probs)

    def error(scaling_factor):
        scaled_probs = base_probs * scaling_factor
        scaled_probs /= np.sum(scaled_probs)  # Normalize
        return abs(calculate_expected(scaled_probs) - expected_runs)

    result = minimize(error, 1.0, bounds=[(0, None)]) # find the scaling factor that reduces the error

    if result.success:
        scaling_factor = result.x[0]
        scaled_probs = base_probs * scaling_factor
        scaled_probs /= np.sum(scaled_probs) # re normalize
        return scaled_probs
    else:
        # Fallback to a basic heuristic if optimization fails
        if expected_runs <= 0:
            return np.array([1, 0, 0, 0, 0, 0])
        elif expected_runs >= 6:
            return np.array([0, 0, 0, 0, 0, 1])
        else:
            # A very simple linear approximation
            p6 = expected_runs / 6.0
            p0 = 1 - p6
            return np.array([p0, 0, 0, 0, 0, p6])

def get_ball_probabilities(expected_runs):
    """Adjust ball probabilities for ODI scoring patterns."""
    if expected_runs <= 0:
        return [1, 0, 0, 0, 0, 0, 0]  # All dots

    # ODI base probabilities - tuned for ODI style
    p0 = 0.68  # Increased dot ball probability for ODIs
    p1 = 0.25 # Increased single probability for ODIs - Strike rotation is key
    p2 = 0.04 # Slightly reduced doubles
    p3 = 0.005 # Very rare in ODIs, keep low
    p4 = 0.02  # Reduced fours, less boundary-focused than T20
    p6 = 0.005 # Significantly reduced sixes for ODI realism

    # Calculate current expected value
    current_exp = 0*p0 + 1*p1 + 2*p2 + 3*p3 + 4*p4 + 6*p6

    # Adjust probabilities to match expected runs
    scale = expected_runs / current_exp if current_exp > 0 else 0

    # Scale all non-zero probabilities
    p1 *= scale
    p2 *= scale
    p3 *= scale
    p4 *= scale
    p6 *= scale

    # Put remaining probability into dots
    p0 = 1 - (p1 + p2 + p3 + p4 + p6)

    return [p0, p1, p2, p3, p4, 0, p6]

def simulate_ball_test(striker, bowler, pitch, settled_meter, over, aggression):
    """
    Simulate a single ball in an ODI match.

    Parameters:
    - striker (Player): The batter facing the ball.
    - bowler (Player): The player bowling the ball.
    - pitch (Stadium): The pitch conditions.
    - settled_meter (float): How settled the batter is (currently unused).
    - over (int): Current over number (currently unused).

    Returns:
    - runs (int): Number of runs scored on this ball (0, 1, 2, 4, or 6).
    - out (bool): Whether the batter is out on this ball.
    - comments (list): a list of strings containing relevant lines of commentary
    - pace (float): speed of the ball
    """
    # Calculate base runs and out probabilities from striker's ODI stats
    base_runs = striker.test_sr / 100  # Expected runs per ball
    base_out = base_runs/ striker.test_ave # Base probability of getting out
    turn, swing, seam, bounce, slower = 0, 0, 0, 0, False
    comments = []

    # Calculate ball attributes based on bowler type and pitch conditions
    if bowler.bowling_type == "Pace":
        # Pace bowler: calculate pace, swing, bounce, and accuracy
        if random.randint(1, 100) < 95:
            # 15% chance of bowling faster
            pace = bowler.bowling_pace - random.gauss(bowler.match_fatigue/10, 5)
            difficulty = max(0,(pace - 130))**1.23 # -5/30
            pd = difficulty
            slower = False
        else:
            # 85% chance of bowling slower with variation
            pace = bowler.bowling_pace * 0.83 + random.gauss(2, 8)
            difficulty = (bowler.bowling_pace - pace)/3
            pd = difficulty
            slower = True 
            #print("s", end = '')
        
        #print(bowler.name, pace, difficulty)
        # Swing and bounce influenced by pitch grass cover and bounce
        swing = ((bowler.bowling_swing -50)**2 * (pitch.grass_cover))/(50 + (over%80) * 20)* random.gauss(1, 0.2)
        difficulty += max(swing, 0.8)
        bounce = ((bowler.bowling_bounce - 50) + (pitch.bounce)) * random.gauss(1, 0.4) * 0.1
        seam = (((bowler.bowling_seam - 50) * (pitch.hardness))/40) ** random.gauss(0, 0.9)
        # Accuracy based on bowler's control
        difficulty += bounce + seam
        #difficulty = max(random.gauss(difficulty,100-bowler.control),difficulty)

        # Calculate difficulty of the ball for the batter
        # Higher pace, swing, bounce, and accuracy increase difficulty
        # Batter's bonuses (batting_fast, batting_swing, batting_bounce) reduce difficulty
        #print(f"Bowler: {bowler.name} Pace:{pd} swing:{swing} Bounce:{bounce} Seam:{seam} difficulty: {difficulty}")
        batter_bonus = ((striker.batting_fast-50) * (pace-130))/40 #
        batter_bonus += ((striker.batting_swing-50) * swing)/20
        batter_bonus += ((striker.batting_bounce-50) * bounce)/30  #print(f"Bowler: {bowler.name} difficulty: {difficulty} batter {batter_bonus}")
    else:
        # Spin bowler: calculate pace (slower), turn, bounce, and accuracy
        pace = bowler.bowling_pace + random.gauss(10, 5)  # Spin pace typically between 60-80 kmph
        turn = max(bowler.bowling_turn * ((pitch.turn)/5)**1.5 * random.gauss(3, 2), 0.2)/100
        difficulty = (turn**1.1)*6.5
        #difficulty = max(random.gauss(difficulty,100-bowler.bowling_control),difficulty)

        batter_bonus = (striker.batting_spin-50)
        #print(f"Bowler: {bowler.name} difficulty: {difficulty} batter {batter_bonus}")
    difficulty *= (random.gauss(bowler.bowling_control, 5)/100)
    batter_bonus += 4*(settled_meter**0.05)

    #print(f"Bowler: {bowler.name} difficulty: {difficulty} batter {batter_bonus}")
    if bowler.match_fatigue > 20:
        bowlfmod = (bowler.match_fatigue-20)/60 #0 to 2+ 
        bowlfmod = max(0,min(bowlfmod,2))
    else: 
        bowlfmod = (20-bowler.match_fatigue)/30 # 1 to 0
        bowlfmod = min(max(bowlfmod,0.1),1)

    if striker.match_fatigue > 20:
        batfmod = (striker.match_fatigue-20)/80 #0 to 2+ 
        batfmod = max(0,min(batfmod,2))
    else: 
        batfmod = (20-striker.match_fatigue)/40 # 1 to 0
        batfmod = min(max(batfmod,0.1),0)

    #print(batfmod, bowlfmod)
    fatigue_effect = ((batfmod - bowlfmod + 3)/3) #  1.4 to 0.6

    if bowler.match_fatigue > 20:
        bowlfmod = (bowler.match_fatigue-20)/60 #0 to 2+ 
        bowlfmod = max(0,min(bowlfmod,2))
    else: 
        bowlfmod = (20-bowler.match_fatigue)/30 # 1 to 0
        bowlfmod = min(max(bowlfmod,0.1),1)

    if striker.match_fatigue > 20:
        batfmod = (striker.match_fatigue-20)/80 #0 to 2+ 
        batfmod = max(0,min(batfmod,2))
    else: 
        batfmod = (20-striker.match_fatigue)/40 # 1 to 0
        batfmod = min(max(batfmod,0.1),0)



    fatigue_effect = ((batfmod - bowlfmod + 3)/3)**0.2 #  1.4 to 0.6

    # Scale factor for difficulty (may need tuning based on testing)
    shot = batter_bonus - (difficulty)
    
    # Calculate probability of getting out
    # Higher difficulty increases the chance of getting out

    p_out = base_out/fatigue_effect * (0.8 - (shot)/50)
    # Determine if the batter is out
    if random.random() < p_out:
        if pace > 145: 
            comments.extend(commentary["very_fast_ball"])
        if swing > 20: 
            comments.extend(commentary["swinging_ball"])
        if slower:
            comments.extend(commentary["slower_ball"])
        if seam > 10: 
            comments.extend(commentary["seaming_ball"])
        if bounce > 10: 
            comments.extend(commentary["high_bouncer"])
        if turn > 3: 
            comments.extend(commentary["spinning_ball"])
        if difficulty < 8: 
            if bowler.bowling_type == "Pacer":
                comments.extend(commentary["bad_ball_pacer"])
            else:
                comments.extend(commentary["bad_ball_spinner"])

        if len(comments) == 0: 
            comments.extend(generic_commentary["W"])

        return 0, True, comments, pace



    runs = base_runs * (1 + shot/100) 


    w = get_ball_probabilities(runs)
    r =  random.choices([0,1,2,3,4,5,6], weights=w)[0]


    if r == 0: 
        if pace > 150: 
            comments.extend(dot_ball_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(dot_ball_commentary["swinging_ball"])
        if slower:
            comments.extend(dot_ball_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(dot_ball_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(dot_ball_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(dot_ball_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(dot_ball_commentary["bad_ball_pacer"])
            else:
                comments.extend(dot_ball_commentary["bad_ball_spinner"])

    
    if r == 1: 
        if pace > 147: 
            comments.extend(single_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(single_commentary["swinging_ball"])
        if slower:
            comments.extend(single_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(single_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(single_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(single_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(single_commentary["bad_ball_pacer"])
            else:
                comments.extend(single_commentary["bad_ball_spinner"])

    if r == 2: 
        if pace > 147: 
            comments.extend(two_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(two_commentary["swinging_ball"])
        if slower:
            comments.extend(two_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(two_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(two_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(two_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(two_commentary["bad_ball_pacer"])
            else:
                comments.extend(two_commentary["bad_ball_spinner"])

    if r == 3:
        if pace > 147: 
            comments.extend(three_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(three_commentary["swinging_ball"])
        if slower:
            comments.extend(three_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(three_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(three_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(three_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(three_commentary["bad_ball_pacer"])
            else:
                comments.extend(three_commentary["bad_ball_spinner"])

    if r == 4: 
        if pace > 147: 
            comments.extend(four_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(four_commentary["swinging_ball"])
        if slower:
            comments.extend(four_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(four_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(four_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(four_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(four_commentary["bad_ball_pacer"])
            else:
                comments.extend(four_commentary["bad_ball_spinner"])

    if r == 6:
        if pace > 147: 
            comments.extend(six_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(six_commentary["swinging_ball"])
        if slower:
            comments.extend(six_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(six_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(six_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(six_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(six_commentary["bad_ball_pacer"])
            else:
                comments.extend(six_commentary["bad_ball_spinner"])

    if len(comments) == 0: 
        if r == 0:
            comments.extend(generic_commentary["."])
        elif r == 1: 
            comments.extend(generic_commentary["1"])
        elif r == 2: 
            comments.extend(generic_commentary["2"])
        elif r == 3: 
            comments.extend(generic_commentary["3"])
        elif r == 4: 
            comments.extend(generic_commentary["4"])
        elif r == 6: 
            comments.extend(generic_commentary["6"])
    return r, False, comments, pace


def simulate_ball_odi(striker, bowler, pitch, settled_meter, over, aggression):
    """
    Simulate a single ball in an ODI match.

    Parameters:
    - striker (Player): The batter facing the ball.
    - bowler (Player): The player bowling the ball.
    - pitch (Stadium): The pitch conditions.
    - settled_meter (float): How settled the batter is (currently unused).
    - over (int): Current over number (currently unused).

    Returns:
    - runs (int): Number of runs scored on this ball (0, 1, 2, 4, or 6).
    - out (bool): Whether the batter is out on this ball.
    - comments (list): a list of strings containing relevant lines of commentary
    - pace (float): speed of the ball
    """
    # Calculate base runs and out probabilities from striker's ODI stats
    base_runs = striker.odi_sr / 100  # Expected runs per ball
    base_out = base_runs * 40 / striker.odi_ave ** 2 # Base probability of getting out
    turn, swing, seam, bounce, slower = 0, 0, 0, 0, False
    comments = []

    # Calculate ball attributes based on bowler type and pitch conditions
    if bowler.bowling_type == "Pace":
        # Pace bowler: calculate pace, swing, bounce, and accuracy
        if random.randint(1, 100) < 87:
            # 15% chance of bowling faster
            pace = bowler.bowling_pace + random.gauss(0, 5)
            difficulty = max(0,(pace - 130))**1.15 # -5/30
            pd = difficulty
            slower = False
        else:
            # 85% chance of bowling slower with variation
            pace = bowler.bowling_pace * 0.83 + random.gauss(2, 8)
            difficulty = (bowler.bowling_pace - pace)/3
            pd = difficulty
            slower = True 
            #print("s", end = '')
        
        #print(bowler.name, pace, difficulty)
        # Swing and bounce influenced by pitch grass cover and bounce
        swing = ((bowler.bowling_swing -50)**2 * (pitch.grass_cover))/(50 + over * 70)* random.gauss(1, 0.2)
        difficulty *= max(swing, 0.8)
        bounce = ((bowler.bowling_bounce)/10 + (pitch.bounce)) * random.gauss(1, 0.4)
        seam = (((bowler.bowling_seam) * (pitch.hardness))/40) ** random.gauss(-0.2, 0.9)
        # Accuracy based on bowler's control
        difficulty += bounce + seam
        #difficulty = max(random.gauss(difficulty,100-bowler.control),difficulty)

        # Calculate difficulty of the ball for the batter
        # Higher pace, swing, bounce, and accuracy increase difficulty
        # Batter's bonuses (batting_fast, batting_swing, batting_bounce) reduce difficulty
        #print(f"Bowler: {bowler.name} Pace:{pd} swing:{swing} Bounce:{bounce} Seam:{seam} difficulty: {difficulty}")
        batter_bonus = ((striker.batting_fast-50) * (pace-130))/25 #
        batter_bonus += ((striker.batting_swing-50) * swing)/10
        batter_bonus += ((striker.batting_bounce-50) * bounce)/140
        #print(f"Bowler: {bowler.name} difficulty: {difficulty} batter {batter_bonus}")
    else:
        # Spin bowler: calculate pace (slower), turn, bounce, and accuracy
        pace = bowler.bowling_pace + random.gauss(10, 5)  # Spin pace typically between 60-80 kmph
        turn = max(bowler.bowling_turn * ((pitch.turn)/5)**1.5 * random.gauss(3, 2), 0.2)/100
        difficulty = (turn**1.1)*4
        #difficulty = max(random.gauss(difficulty,100-bowler.bowling_control),difficulty)

        batter_bonus = (striker.batting_spin-50)
        #print(f"Bowler: {bowler.name} difficulty: {difficulty} batter {batter_bonus}")

    batter_bonus += 3*(settled_meter**0.15)

    #print(f"Bowler: {bowler.name} difficulty: {difficulty} batter {batter_bonus}")
    if bowler.match_fatigue > 20:
        bowlfmod = (bowler.match_fatigue-20)/60 #0 to 2+ 
        bowlfmod = max(0,min(bowlfmod,2))
    else: 
        bowlfmod = (20-bowler.match_fatigue)/30 # 1 to 0
        bowlfmod = min(max(bowlfmod,0.1),1)

    if striker.match_fatigue > 20:
        batfmod = (striker.match_fatigue-20)/80 #0 to 2+ 
        batfmod = max(0,min(batfmod,2))
    else: 
        batfmod = (20-striker.match_fatigue)/40 # 1 to 0
        batfmod = min(max(batfmod,0.1),0)



    fatigue_effect = ((batfmod - bowlfmod + 3)/3)**0.2 #  1.4 to 0.6


    # Scale factor for difficulty (may need tuning based on testing)
    shot = batter_bonus - (difficulty)
    
    # Calculate probability of getting out
    # Higher difficulty increases the chance of getting out
    #print(shot)
    #print(f"{difficulty} Shot:{shot} Swing{swing}")
    aggression = aggression
    p_out = min(3*base_out*aggression, base_out * (0.6 - (shot)/80) * (aggression ** 0.8)) 

    # Determine if the batter is out
    if random.random() < p_out:
        if pace > 145: 
            comments.extend(commentary["very_fast_ball"])
        if swing > 20: 
            comments.extend(commentary["swinging_ball"])
        if slower:
            comments.extend(commentary["slower_ball"])
        if seam > 10: 
            comments.extend(commentary["seaming_ball"])
        if bounce > 10: 
            comments.extend(commentary["high_bouncer"])
        if turn > 3: 
            comments.extend(commentary["spinning_ball"])
        if difficulty < 8: 
            if bowler.bowling_type == "Pacer":
                comments.extend(commentary["bad_ball_pacer"])
            else:
                comments.extend(commentary["bad_ball_spinner"])

        if len(comments) == 0: 
            comments.extend(generic_commentary["W"])

        return 0, True, comments, pace

    runs = (base_runs)**2 * (1 + shot/80)*fatigue_effect * max(aggression, aggression ** 1.2)
    w = get_ball_probabilities(runs)
    r =  random.choices([0,1,2,3,4,5,6], weights=w)[0]

    if r == 0: 
        if random.randint(1,100) > (striker.batting_rotation - 50):
            r = 1
    if r == 1:
        if random.randint(1,100) < (striker.batting_rotation - 50):
            r = 0

    if r == 0: 
        if pace > 150: 
            comments.extend(dot_ball_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(dot_ball_commentary["swinging_ball"])
        if slower:
            comments.extend(dot_ball_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(dot_ball_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(dot_ball_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(dot_ball_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(dot_ball_commentary["bad_ball_pacer"])
            else:
                comments.extend(dot_ball_commentary["bad_ball_spinner"])

    
    if r == 1: 
        if pace > 147: 
            comments.extend(single_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(single_commentary["swinging_ball"])
        if slower:
            comments.extend(single_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(single_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(single_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(single_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(single_commentary["bad_ball_pacer"])
            else:
                comments.extend(single_commentary["bad_ball_spinner"])

    if r == 2: 
        if pace > 147: 
            comments.extend(two_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(two_commentary["swinging_ball"])
        if slower:
            comments.extend(two_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(two_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(two_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(two_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(two_commentary["bad_ball_pacer"])
            else:
                comments.extend(two_commentary["bad_ball_spinner"])

    if r == 3:
        if pace > 147: 
            comments.extend(three_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(three_commentary["swinging_ball"])
        if slower:
            comments.extend(three_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(three_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(three_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(three_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(three_commentary["bad_ball_pacer"])
            else:
                comments.extend(three_commentary["bad_ball_spinner"])

    if r == 4: 
        if pace > 147: 
            comments.extend(four_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(four_commentary["swinging_ball"])
        if slower:
            comments.extend(four_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(four_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(four_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(four_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(four_commentary["bad_ball_pacer"])
            else:
                comments.extend(four_commentary["bad_ball_spinner"])

    if r == 6:
        if pace > 147: 
            comments.extend(six_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(six_commentary["swinging_ball"])
        if slower:
            comments.extend(six_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(six_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(six_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(six_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(six_commentary["bad_ball_pacer"])
            else:
                comments.extend(six_commentary["bad_ball_spinner"])

    if len(comments) == 0: 
        if r == 0:
            comments.extend(generic_commentary["."])
        elif r == 1: 
            comments.extend(generic_commentary["1"])
        elif r == 2: 
            comments.extend(generic_commentary["2"])
        elif r == 3: 
            comments.extend(generic_commentary["3"])
        elif r == 4: 
            comments.extend(generic_commentary["4"])
        elif r == 6: 
            comments.extend(generic_commentary["6"])
    return r, False, comments, pace


def simulate_ball_t20(striker, bowler, pitch, settled_meter, over, aggression):
    """
    Simulate a single ball in an ODI match.

    Parameters:
    - striker (Player): The batter facing the ball.
    - bowler (Player): The player bowling the ball.
    - pitch (Stadium): The pitch conditions.
    - settled_meter (float): How settled the batter is (currently unused).
    - over (int): Current over number (currently unused).

    Returns:
    - runs (int): Number of runs scored on this ball (0, 1, 2, 4, or 6).
    - out (bool): Whether the batter is out on this ball.
    - comments (list): a list of strings containing relevant lines of commentary
    - pace (float): speed of the ball
    """
    # Calculate base runs and out probabilities from striker's ODI stats
    base_runs = (striker.t20_sr)/ 100  # Expected runs per ball
    base_out = base_runs/striker.t20_ave  # Base probability of getting out
    turn, swing, seam, bounce, slower = 0, 0, 0, 0, False
    comments = []

    # Calculate ball attributes based on bowler type and pitch conditions
    if bowler.bowling_type == "Pace":
        # Pace bowler: calculate pace, swing, bounce, and accuracy
        if random.randint(1, 100) < 87:
            # 15% chance of bowling faster
            pace = bowler.bowling_pace + random.gauss(0, 5)
            difficulty = max(0,(pace - 130))**1.15 # -5/30
            pd = difficulty
            slower = False
        else:
            # 85% chance of bowling slower with variation
            pace = bowler.bowling_pace * 0.83 + random.gauss(2, 8)
            difficulty = (bowler.bowling_pace - pace)/3
            pd = difficulty
            slower = True 
            #print("s", end = '')
        
        #print(bowler.name, pace, difficulty)
        # Swing and bounce influenced by pitch grass cover and bounce
        swing = ((bowler.bowling_swing - 50)**2 * (pitch.grass_cover))/(50 + over * 70)* random.gauss(1, 0.2)
        difficulty *= max(swing, 0.8)
        bounce = ((bowler.bowling_bounce)/10 + (pitch.bounce)) * random.gauss(1, 0.4)
        seam = (((bowler.bowling_seam) * (pitch.hardness))/40) ** random.gauss(-0.2, 0.9)
        # Accuracy based on bowler's control
        difficulty += bounce + seam
        #difficulty = max(random.gauss(difficulty,100-bowler.control),difficulty)

        # Calculate difficulty of the ball for the batter
        # Higher pace, swing, bounce, and accuracy increase difficulty
        # Batter's bonuses (batting_fast, batting_swing, batting_bounce) reduce difficulty
        #print(f"Bowler: {bowler.name} Pace:{pd} swing:{swing} Bounce:{bounce} Seam:{seam} difficulty: {difficulty}")
        batter_bonus = (striker.batting_fast * (pace-130))/25
        batter_bonus += (striker.batting_swing * swing)/10
        batter_bonus += (striker.batting_bounce * bounce)/140
        #print(f"Bowler: {bowler.name} difficulty: {difficulty} batter {batter_bonus}")
    else:
        # Spin bowler: calculate pace (slower), turn, bounce, and accuracy
        pace = bowler.bowling_pace + random.gauss(10, 5)  # Spin pace typically between 60-80 kmph
        turn = max(bowler.bowling_turn * ((pitch.turn)/5)**1.5 * random.gauss(3, 2), 0.2)/100
        difficulty = (turn**1.1)*4
        #difficulty = max(random.gauss(difficulty,100-bowler.bowling_control),difficulty)

        batter_bonus = striker.batting_spin/6
        #print(f"Bowler: {bowler.name} difficulty: {difficulty} batter {batter_bonus}")
    batter_bonus += 3.5*(settled_meter**0.2)

    #print(f"Bowler: {bowler.name} difficulty: {difficulty} batter {batter_bonus}")
    if bowler.match_fatigue > 20:
        bowlfmod = (bowler.match_fatigue-20)/60 #0 to 2+ 
        bowlfmod = max(0,min(bowlfmod,2))
    else: 
        bowlfmod = (20-bowler.match_fatigue)/30 # 1 to 0
        bowlfmod = min(max(bowlfmod,0.1),1)

    if striker.match_fatigue > 20:
        batfmod = (striker.match_fatigue-20)/80 #0 to 2+ 
        batfmod = max(0,min(batfmod,2))
    else: 
        batfmod = (20-striker.match_fatigue)/40 # 1 to 0
        batfmod = min(max(batfmod,0.1),0)



    fatigue_effect = ((batfmod - bowlfmod + 3)/3)**0.2 #  1.4 to 0.6


    # Scale factor for difficulty (may need tuning based on testing)
    shot = batter_bonus - (difficulty)
    
    # Calculate probability of getting out
    # Higher difficulty increases the chance of getting out
    p_out = min(2*base_out*aggression**2, base_out * (1 - (shot)/100) * (aggression ** 2))
    if settled_meter < 20: 
        p_out /= (striker.t20_ave/15)
    # Determine if the batter is out
    if random.random() < p_out:
        if pace > 145: 
            comments.extend(commentary["very_fast_ball"])
        if swing > 20: 
            comments.extend(commentary["swinging_ball"])
        if slower:
            comments.extend(commentary["slower_ball"])
        if seam > 10: 
            comments.extend(commentary["seaming_ball"])
        if bounce > 10: 
            comments.extend(commentary["high_bouncer"])
        if turn > 3: 
            comments.extend(commentary["spinning_ball"])
        if difficulty < 8: 
            if bowler.bowling_type == "Pacer":
                comments.extend(commentary["bad_ball_pacer"])
            else:
                comments.extend(commentary["bad_ball_spinner"])

        if len(comments) == 0: 
            comments.extend(generic_commentary["W"])

        return 0, True, comments, pace

    runs = ((base_runs+0.1)**1.17+0.1) * (1.6+ shot/100)*fatigue_effect * (aggression+0.1) ** 1.5
    w = get_ball_probabilities(runs)
    r =  random.choices([0,1,2,3,4,5,6], weights=w)[0]

    if r == 0: 
        if random.randint(1,100) > (striker.batting_rotation - 50):
            r = 1
    if r == 1:
        if random.randint(1,100) < (striker.batting_rotation - 50):
            r = 0

    if r == 0: 
        if pace > 150: 
            comments.extend(dot_ball_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(dot_ball_commentary["swinging_ball"])
        if slower:
            comments.extend(dot_ball_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(dot_ball_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(dot_ball_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(dot_ball_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(dot_ball_commentary["bad_ball_pacer"])
            else:
                comments.extend(dot_ball_commentary["bad_ball_spinner"])

    
    if r == 1: 
        if pace > 147: 
            comments.extend(single_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(single_commentary["swinging_ball"])
        if slower:
            comments.extend(single_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(single_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(single_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(single_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(single_commentary["bad_ball_pacer"])
            else:
                comments.extend(single_commentary["bad_ball_spinner"])

    if r == 2: 
        if pace > 147: 
            comments.extend(two_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(two_commentary["swinging_ball"])
        if slower:
            comments.extend(two_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(two_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(two_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(two_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(two_commentary["bad_ball_pacer"])
            else:
                comments.extend(two_commentary["bad_ball_spinner"])

    if r == 3:
        if pace > 147: 
            comments.extend(three_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(three_commentary["swinging_ball"])
        if slower:
            comments.extend(three_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(three_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(three_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(three_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(three_commentary["bad_ball_pacer"])
            else:
                comments.extend(three_commentary["bad_ball_spinner"])

    if r == 4: 
        if pace > 147: 
            comments.extend(four_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(four_commentary["swinging_ball"])
        if slower:
            comments.extend(four_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(four_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(four_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(four_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(four_commentary["bad_ball_pacer"])
            else:
                comments.extend(four_commentary["bad_ball_spinner"])

    if r == 6:
        if pace > 147: 
            comments.extend(six_commentary["very_fast_ball"])
        if swing > 22: 
            comments.extend(six_commentary["swinging_ball"])
        if slower:
            comments.extend(six_commentary["slower_ball"])
        if seam > 12: 
            comments.extend(six_commentary["seaming_ball"])
        if bounce > 7: 
            comments.extend(six_commentary["high_bouncer"])
        if turn > 10: 
            comments.extend(six_commentary["spinning_ball"])
        if difficulty < 8:
            if bowler.bowling_type == "Pacer":
                comments.extend(six_commentary["bad_ball_pacer"])
            else:
                comments.extend(six_commentary["bad_ball_spinner"])

    if len(comments) == 0: 
        if r == 0:
            comments.extend(generic_commentary["."])
        elif r == 1: 
            comments.extend(generic_commentary["1"])
        elif r == 2: 
            comments.extend(generic_commentary["2"])
        elif r == 3: 
            comments.extend(generic_commentary["3"])
        elif r == 4: 
            comments.extend(generic_commentary["4"])
        elif r == 6: 
            comments.extend(generic_commentary["6"])
    return r, False, comments, pace


def simulate_odi(team1, team2, venue):
    """Simulate a match between any two teams."""
    # Random toss to decide who bats first
    if random.randint(1, 100) > 100:
        team1, team2 = team2, team1
    
    pitch = venue
    
    # Simulate first innings
    team1_score, team1_wickets, team1_batting_stats, team1_bowling_stats = simulate_odi_innings(team1, team2, pitch)
    
    # Display scorecard for team 1
    display_scorecard(team1_batting_stats, team1_bowling_stats, team1.name, team1_score, team1_wickets, [])
    
    # Simulate second innings
    team2_score, team2_wickets, team2_batting_stats, team2_bowling_stats = simulate_odi_innings(team2, team1, pitch, team1_score)

    
    # Display scorecard for team 2
    display_scorecard(team2_batting_stats, team2_bowling_stats, team2.name, team2_score, team2_wickets, [])

    # Determine winner
    if team1_score > team2_score:
        print(f"\n{team1.name} wins by {team1_score - team2_score} runs!")
    elif team2_score > team1_score:
        print(f"\n{team2.name} wins by {10 - team2_wickets} wickets!")
    else:
        print("\nMatch tied!")
    
    return (team1_score, team1_wickets, team2_score, team2_wickets)


def simulate_t20(team1, team2, venue):
    """Simulate a match between any two teams."""
    # Random toss to decide who bats first
    if random.randint(1, 100) > 100:
        team1, team2 = team2, team1
    
    pitch = venue
    
    # Simulate first innings
    team1_score, team1_wickets, team1_batting_stats, team1_bowling_stats = simulate_t20_innings(team1, team2, pitch)
    
    # Display scorecard for team 1
    display_scorecard(team1_batting_stats, team1_bowling_stats, team1.name, team1_score, team1_wickets, [])
    
    # Simulate second innings
    team2_score, team2_wickets, team2_batting_stats, team2_bowling_stats = simulate_t20_innings(team2, team1, pitch, team1_score)

    
    # Display scorecard for team 2
    display_scorecard(team2_batting_stats, team2_bowling_stats, team2.name, team2_score, team2_wickets, [])

    # Determine winner
    if team1_score > team2_score:
        print(f"\n{team1.name} wins by {team1_score - team2_score} runs!")
    elif team2_score > team1_score:
        print(f"\n{team2.name} wins by {10 - team2_wickets} wickets!")
    else:
        print("\nMatch tied!")
    
    return (team1_score, team1_wickets, team2_score, team2_wickets)


def select_bowler_test(bowling_team, bowled_overs, over_number, previous_bowler, bowling_stats):
    """
    Select the best bowler for the current over in an ODI match.

    Parameters:
    - bowling_team (Team): The team bowling, with Player objects in team.players.
    - bowled_overs (dict): Dictionary mapping bowler names to the number of overs they’ve bowled.
    - over_number (int): The current over number (0 to 49).
    - previous_bowler (Player or None): The bowler who bowled the previous over (None for first over).
    - bowling_stats (dict): Dictionary of bowler performance stats {name: {"overs": int, "m": int, "runs": int, "wickets": int}}.

    Returns:
    - Player: The selected bowler as a Player object.
    """
    # Step 1: Filter available bowlers based on constraints
    available_bowlers = []
    for player in bowling_team.players:
        name = player.name
        overs_bowled = bowled_overs.get(name, 0)
        
        # Exclude if bowled 10 overs or was the previous bowler
        if (previous_bowler is None or name != previous_bowler.name):
            available_bowlers.append(player)
    
    if not available_bowlers:
        raise ValueError("No available bowlers meet the criteria!")

    # Step 2: Define situational weights based on over number
    if over_number % 80 < 30:  # Powerplay (overs 0-9)
        # Favor pace bowlers with swing/control for early wickets
        situation_weights = {
            "pace": 1.5,         # Boost for pace bowlers
            "swing": 1.8,        # Swing to exploit new ball
            "control": 1.3,      # Accuracy for tight lines
            "wickets": 0.5,      # Prioritize wicket-taking
            "economy": 0.6,  
            "spin": -0.5     # Less focus on economy early
        }
    else:  
        # Middle overs (10-39)
        # Balance between spin/pace, wickets, and economy
        situation_weights = {
            "pace": 1.0,
            "swing": 0.8,
            "control": 1.2,
            "wickets": 0.5,
            "economy": 1,
            "spin": 1.3       # Control runs in middle phase
        }


    bowler_scores = []
    for bowler in available_bowlers:
        name = bowler.name
        stats = bowling_stats.get(name, {"overs": 0, "runs": 0, "wickets": 0})
        
        # Base ability scores from Player attributes
        pace_score = max(0, bowler.bowling_pace - 125) ** 0.2
        swing = (bowler.bowling_swing  - 60)/20 if hasattr(bowler, 'bowling_swing') else bowler.bowling_turn / 100  # Use turn for spinners
        control_score = (bowler.bowling_control - 60) / 20
        spin_score = (bowler.bowling_turn - 60) / 20
        
        # Performance scores from current match
        overs_bowled = stats["overs"]
        wickets = stats["wickets"]
        runs = stats["runs"]
        economy = (max(0,(runs - overs_bowled * 3)))/(overs_bowled+1)
        
        # Normalize performance: reward wickets, penalize high economy
        wicket_score = min(wickets / 5, 1.0)  # Cap at 5 wickets for max score
        economy_score = max(0, 1 - (economy - 6) / 6)  # Ideal economy ~6, penalize above
        
        bs = 2
        if bowler.role == "Bowler": 
            bs = 4
        if bowler.role == "Batsman": 
            bs = 0
        # Combine scores with situational weights
        total_score = (
            situation_weights["pace"] * pace_score +
            situation_weights["swing"] * swing +
            situation_weights["control"] * control_score +
            situation_weights["wickets"] * wicket_score +
            situation_weights["economy"] * economy_score +
            situation_weights["spin"] * spin_score + bs
            - (bowler.match_fatigue)**0.3

        )
        
        # Adjust for freshness: slightly favor bowlers who’ve bowled less
        total_score = total_score
        
        bowler_scores.append((bowler, total_score))
        if bowler.match_fatigue > 20:
            bowler.match_fatigue -= 2

    # Step 4: Select top candidates and add randomness for variety
    if not bowler_scores:
        raise ValueError("No bowlers could be scored!")
    
    # Sort by score descending
    bowler_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Pick from top 3 (or fewer) to avoid always choosing the same bowler
    top_n = min(3, len(bowler_scores))
    top_bowlers = bowler_scores[:top_n]
    selected_bowler = random.choices(
        [b[0] for b in top_bowlers], 
        weights=[max(0.01,b[1]) for b in top_bowlers], 
        k=1
    )[0]

    # Debug output (optional)
    # print(f"Over {over_number + 1}: Selected {selected_bowler.name} (Score: {dict(bowler_scores)[selected_bowler]:.2f})")
    selected_bowler.match_fatigue += 500/selected_bowler.fitness
    return selected_bowler


def select_bowler_odi(bowling_team, bowled_overs, over_number, previous_bowler, bowling_stats):
    """
    Select the best bowler for the current over in an ODI match.

    Parameters:
    - bowling_team (Team): The team bowling, with Player objects in team.players.
    - bowled_overs (dict): Dictionary mapping bowler names to the number of overs they’ve bowled.
    - over_number (int): The current over number (0 to 49).
    - previous_bowler (Player or None): The bowler who bowled the previous over (None for first over).
    - bowling_stats (dict): Dictionary of bowler performance stats {name: {"overs": int, "m": int, "runs": int, "wickets": int}}.

    Returns:
    - Player: The selected bowler as a Player object.
    """
    # Step 1: Filter available bowlers based on constraints
    available_bowlers = []
    for player in bowling_team.players:
        name = player.name
        overs_bowled = bowled_overs.get(name, 0)
        
        # Exclude if bowled 10 overs or was the previous bowler
        if (previous_bowler is None or name != previous_bowler.name) and (overs_bowled < 10):
            available_bowlers.append(player)
    
    if not available_bowlers:
        raise ValueError("No available bowlers meet the criteria!")

    # Step 2: Define situational weights based on over number
    if over_number < 10:  # Powerplay (overs 0-9)
        # Favor pace bowlers with swing/control for early wickets
        situation_weights = {
            "pace": 1.5,         # Boost for pace bowlers
            "swing": 1.8,        # Swing to exploit new ball
            "control": 1.3,      # Accuracy for tight lines
            "wickets": 1.2,      # Prioritize wicket-taking
            "economy": 0.6,  
            "spin": -0.3     # Less focus on economy early
        }
    elif over_number < 40:  
        # Middle overs (10-39)
        # Balance between spin/pace, wickets, and economy
        situation_weights = {
            "pace": 1.0,
            "swing": 0.8,
            "control": 1.2,
            "wickets": 0.5,
            "economy": 1,
            "spin": 1.5        # Control runs in middle phase
        }

    else:  
        # Middle overs (10-39)
        # Balance between spin/pace, wickets, and economy
        situation_weights = {
            "pace": 1.3,
            "swing": 0.4,
            "control": 1.5,
            "wickets": 0.5,
            "economy": 1.3,
            "spin": 0.3       # Control runs in middle phase
        }
    bowler_scores = []
    for bowler in available_bowlers:
        name = bowler.name
        stats = bowling_stats.get(name, {"overs": 0, "runs": 0, "wickets": 0})
        
        # Base ability scores from Player attributes
        pace_score = bowler.bowling_pace / 100
        swing = bowler.bowling_swing / 100 if hasattr(bowler, 'bowling_swing') else bowler.bowling_turn / 100  # Use turn for spinners
        control_score = bowler.bowling_control / 100
        spin_score = bowler.bowling_turn / 100 
        if bowler.bowling_type =="Finger":
            spin_score = spin_score + 0.3
        
        # Performance scores from current match
        overs_bowled = stats["overs"]
        wickets = stats["wickets"]
        runs = stats["runs"]
        economy = max(0,(runs - overs_bowled * 7))** 0.5
        
        # Normalize performance: reward wickets, penalize high economy
        wicket_score = min(wickets / 5, 1.0)  # Cap at 5 wickets for max score
        economy_score = max(0, 1 - (economy - 6) / 6)  # Ideal economy ~6, penalize above
        
        # Combine scores with situational weights
        total_score = (
            situation_weights["pace"] * pace_score +
            situation_weights["swing"] * swing +
            situation_weights["control"] * control_score +
            situation_weights["wickets"] * wicket_score +
            situation_weights["economy"] * economy_score +
            situation_weights["spin"] * spin_score
        )
        
        # Adjust for freshness: slightly favor bowlers who’ve bowled less
        total_score = total_score - (bowler.match_fatigue*total_score/200)
        
        bowler_scores.append((bowler, total_score))
        if bowler.match_fatigue > 20:
            bowler.match_fatigue -= 2

    # Step 4: Select top candidates and add randomness for variety
    if not bowler_scores:
        raise ValueError("No bowlers could be scored!")
    
    # Sort by score descending
    bowler_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Pick from top 3 (or fewer) to avoid always choosing the same bowler
    top_n = min(3, len(bowler_scores))
    top_bowlers = bowler_scores[:top_n]
    selected_bowler = random.choices(
        [b[0] for b in top_bowlers], 
        weights=[b[1] for b in top_bowlers], 
        k=1
    )[0]

    # Debug output (optional)
    # print(f"Over {over_number + 1}: Selected {selected_bowler.name} (Score: {dict(bowler_scores)[selected_bowler]:.2f})")
    selected_bowler.match_fatigue += 100/selected_bowler.fitness
    return selected_bowler



def select_bowler_t20(bowling_team, bowled_overs, over_number, previous_bowler, bowling_stats):
    """
    Select the best bowler for the current over in an ODI match.

    Parameters:
    - bowling_team (Team): The team bowling, with Player objects in team.players.
    - bowled_overs (dict): Dictionary mapping bowler names to the number of overs they’ve bowled.
    - over_number (int): The current over number (0 to 49).
    - previous_bowler (Player or None): The bowler who bowled the previous over (None for first over).
    - bowling_stats (dict): Dictionary of bowler performance stats {name: {"overs": int, "m": int, "runs": int, "wickets": int}}.

    Returns:
    - Player: The selected bowler as a Player object.
    """
    # Step 1: Filter available bowlers based on constraints
    available_bowlers = []
    for player in bowling_team.players:
        name = player.name
        overs_bowled = bowled_overs.get(name, 0)
        
        # Exclude if bowled 10 overs or was the previous bowler
        if (previous_bowler is None or name != previous_bowler.name) and (overs_bowled < 4):
            available_bowlers.append(player)
    
    if not available_bowlers:
        raise ValueError("No available bowlers meet the criteria!")

    # Step 2: Define situational weights based on over number
    if over_number < 6:  # Powerplay (overs 0-9)
        # Favor pace bowlers with swing/control for early wickets
        situation_weights = {
            "pace": 1.5,         # Boost for pace bowlers
            "swing": 1.8,        # Swing to exploit new ball
            "control": 1.3,      # Accuracy for tight lines
            "wickets": 1.2,      # Prioritize wicket-taking
            "economy": 0.6,  
            "spin": -0.5     # Less focus on economy early
        }
    elif over_number < 15:  
        # Middle overs (10-39)
        # Balance between spin/pace, wickets, and economy
        situation_weights = {
            "pace": 1.0,
            "swing": 0.8,
            "control": 1.2,
            "wickets": 0.5,
            "economy": 1,
            "spin": 1.5        # Control runs in middle phase
        }

    else:  
        # Middle overs (10-39)
        # Balance between spin/pace, wickets, and economy
        situation_weights = {
            "pace": 1.3,
            "swing": 0.4,
            "control": 1.5,
            "wickets": 0.5,
            "economy": 1.3,
            "spin": 0.6        # Control runs in middle phase
        }
    bowler_scores = []
    for bowler in available_bowlers:
        name = bowler.name
        stats = bowling_stats.get(name, {"overs": 0, "runs": 0, "wickets": 0})
        
        # Base ability scores from Player attributes
        pace_score = bowler.bowling_pace / 100
        swing = bowler.bowling_swing / 100 if hasattr(bowler, 'bowling_swing') else bowler.bowling_turn / 100  # Use turn for spinners
        control_score = bowler.bowling_control / 100
        spin_score = bowler.bowling_turn / 100 
        if bowler.bowling_type =="Finger":
            spin_score = spin_score + 0.3
        
        # Performance scores from current match
        overs_bowled = stats["overs"]
        wickets = stats["wickets"]
        runs = stats["runs"]
        economy = max(0,(runs - overs_bowled * 7))** 0.5
        
        # Normalize performance: reward wickets, penalize high economy
        wicket_score = min(wickets / 5, 1.0)  # Cap at 5 wickets for max score
        economy_score = max(0, 1 - (economy - 6) / 6)  # Ideal economy ~6, penalize above
        
        # Combine scores with situational weights
        total_score = (
            situation_weights["pace"] * pace_score +
            situation_weights["swing"] * swing +
            situation_weights["control"] * control_score +
            situation_weights["wickets"] * wicket_score +
            situation_weights["economy"] * economy_score +
            situation_weights["spin"] * spin_score
        )
        
        # Adjust for freshness: slightly favor bowlers who’ve bowled less
        total_score = total_score - (bowler.match_fatigue*total_score/200)
        
        bowler_scores.append((bowler, total_score))
        if bowler.match_fatigue > 20:
            bowler.match_fatigue -= 2

    # Step 4: Select top candidates and add randomness for variety
    if not bowler_scores:
        raise ValueError("No bowlers could be scored!")
    
    # Sort by score descending
    bowler_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Pick from top 3 (or fewer) to avoid always choosing the same bowler
    top_n = min(3, len(bowler_scores))
    top_bowlers = bowler_scores[:top_n]
    selected_bowler = random.choices(
        [b[0] for b in top_bowlers], 
        weights=[b[1] for b in top_bowlers], 
        k=1
    )[0]

    # Debug output (optional)
    # print(f"Over {over_number + 1}: Selected {selected_bowler.name} (Score: {dict(bowler_scores)[selected_bowler]:.2f})")
    selected_bowler.match_fatigue += 100/selected_bowler.fitness
    return selected_bowler




def simulate_t20_innings(batting_team: Team, bowling_team: Team, venue, target=None):
    score = 0
    wickets = 0
    bowled_overs = {}
    batsman_index = 2
    gamewon = False
    bowler = None
    
    batting_stats = {player.name: {"runs": 0, "balls": 0, "out": False} for player in batting_team.players}
    bowling_stats = {player.name: {"overs": 0, "manameens": 0, "runs": 0, "wickets": 0} for player in bowling_team.players}
    settled_meters = {player.name: 0 for player in batting_team.players}

    striker = batting_team.players[0]
    non_striker = batting_team.players[1]
    
    for over in range(20):
        if wickets >= 10 or gamewon:
            break


        bowler = select_bowler_t20(bowling_team, bowled_overs, over, bowler, bowling_stats)
        #print(f"\nOver {over + 1}: {bowler.name} bowling")
        message = ""
        over_runs, over_wickets = 0, 0
        
        for ball in range(6):
            if wickets >= 10 or gamewon:
                break

            batting_stats[striker.name]["balls"] += 1
            aggression = calculate_aggression_t20(over, venue, target, striker, non_striker, settled_meters[striker.name], settled_meters[non_striker.name], 10-wickets, score)
            run, out, comments, pace = simulate_ball_t20(striker, bowler, venue, settled_meters[striker.name], over, aggression)
            #print(f"{over}.{ball+1} {bowler.name} to {striker.name} | {run} Runs. | {pace} {random.choice(comments)} |{score}/{wickets}")
            striker.match_fatigue += 50/striker.fitness
            if run < 4: 
                striker.match_fatigue += run * 70/striker.fitness
                non_striker.match_fatigue += run * 70/non_striker.fitness
            else: 
                striker.match_fatigue += 100/striker.fitness
                non_striker.match_fatigue += 50/non_striker.fitness
            
            
            if out:
                wickets += 1
                batting_stats[striker.name]["out"] = True
                bowling_stats[bowler.name]["wickets"] += 1
                if batsman_index < len(batting_team.players):
                    striker = batting_team.players[batsman_index]
                    settled_meters[striker.name] = 0
                    batsman_index += 1
            else:
                score += run
                batting_stats[striker.name]["runs"] += run
                if target and score > target:
                    gamewon = True
                if settled_meters[striker.name] < 50:
                    settled_meters[striker.name] += 0.4 + run*1.2
                if run % 2 == 1:
                    striker, non_striker = non_striker, striker
            
            over_runs += run
            if out: 
                message += f"{over}.{ball+1} {bowler.name} to {striker.name}: OUT! Score {score}/{wickets}\n"
            else:
                message += f"{over}.{ball+1} {bowler.name} to {striker.name}: {run} Runs. Score {score}/{wickets}\n"
        
        striker, non_striker = non_striker, striker
        bowling_stats[bowler.name]["overs"] += 1
        bowling_stats[bowler.name]["runs"] += over_runs

        message += f"End of Over {over} | Score {score}/{wickets} | {striker.name}:{batting_stats[striker.name]["runs"]}* of {batting_stats[striker.name]["balls"]} | {non_striker.name}:{batting_stats[non_striker.name]["runs"]} of {batting_stats[non_striker.name]["balls"]} | {bowler.name} :  {bowling_stats[bowler.name]["overs"]}-{bowling_stats[bowler.name]["runs"]}-{bowling_stats[bowler.name]["wickets"]}"
        bowled_overs[bowler.name] = bowled_overs.get(bowler.name, 0) + 1
    
    return score, wickets, batting_stats, bowling_stats

def simulate_odi_innings(batting_team: Team, bowling_team: Team, venue, target=None):
    score = 0
    wickets = 0
    bowled_overs = {}
    batsman_index = 2
    gamewon = False
    bowler = None
    
    batting_stats = {player.name: {"runs": 0, "balls": 0, "out": False} for player in batting_team.players}
    bowling_stats = {player.name: {"overs": 0, "manameens": 0, "runs": 0, "wickets": 0} for player in bowling_team.players}
    settled_meters = {player.name: 0 for player in batting_team.players}

    striker = batting_team.players[0]
    non_striker = batting_team.players[1]
    
    for over in range(50):
        if wickets >= 10 or gamewon:
            break


        bowler = select_bowler_odi(bowling_team, bowled_overs, over, bowler, bowling_stats)
        #print(f"\nOver {over + 1}: {bowler.name} bowling")
        message = ""
        over_runs, over_wickets = 0, 0
        
        for ball in range(6):
            if wickets >= 10 or gamewon:
                break

            batting_stats[striker.name]["balls"] += 1
            aggression = calculate_aggression_odi(over, venue, target, striker, non_striker, settled_meters[striker.name], settled_meters[non_striker.name], 10-wickets, score)
            run, out, comments, pace = simulate_ball_odi(striker, bowler, venue, settled_meters[striker.name], over, aggression)
            #print(f"{over}.{ball+1} {bowler.name} to {striker.name} | {run} Runs. | {pace} {random.choice(comments)} |{score}/{wickets}")
            striker.match_fatigue += 20/bowler.fitness
            if run < 4: 
                striker.match_fatigue += run * 40/bowler.fitness
                non_striker.match_fatigue += run * 40/bowler.fitness
            
            
            if out:
                wickets += 1
                batting_stats[striker.name]["out"] = True
                bowling_stats[bowler.name]["wickets"] += 1
                if batsman_index < len(batting_team.players):
                    striker = batting_team.players[batsman_index]
                    settled_meters[striker.name] = 0
                    batsman_index += 1
            else:
                score += run
                batting_stats[striker.name]["runs"] += run
                if target and score > target:
                    gamewon = True
                if settled_meters[striker.name] < 100:
                    settled_meters[striker.name] += run*0.4  + 0.2
                if run % 2 == 1:
                    striker, non_striker = non_striker, striker
            
            over_runs += run
            if out: 
                message += f"{over}.{ball+1} {bowler.name} to {striker.name}: OUT! Score {score}/{wickets}\n"
            else:
                message += f"{over}.{ball+1} {bowler.name} to {striker.name}: {run} Runs. Score {score}/{wickets}\n"
        
        striker, non_striker = non_striker, striker
        bowling_stats[bowler.name]["overs"] += 1
        bowling_stats[bowler.name]["runs"] += over_runs

        message += f"End of Over {over} | Score {score}/{wickets} | {striker.name}:{batting_stats[striker.name]["runs"]}* of {batting_stats[striker.name]["balls"]} | {non_striker.name}:{batting_stats[non_striker.name]["runs"]} of {batting_stats[non_striker.name]["balls"]} | {bowler.name} :  {bowling_stats[bowler.name]["overs"]}-{bowling_stats[bowler.name]["runs"]}-{bowling_stats[bowler.name]["wickets"]}"
        bowled_overs[bowler.name] = bowled_overs.get(bowler.name, 0) + 1
    
    return score, wickets, batting_stats, bowling_stats
        


def simulate_test_innings(batting_team: Team, bowling_team: Team, venue, target=None):
    score = 0
    wickets = 0
    bowled_overs = {}
    batsman_index = 2
    gamewon = False
    bowler = None

    for bowler in bowling_team.players:
        bowler.match_fatigue = 10
    
    batting_stats = {player.name: {"runs": 0, "balls": 0, "out": False} for player in batting_team.players}
    bowling_stats = {player.name: {"overs": 0, "manameens": 0, "runs": 0, "wickets": 0} for player in bowling_team.players}
    settled_meters = {player.name: 0 for player in batting_team.players}

    striker = batting_team.players[0]
    non_striker = batting_team.players[1]
    
    for over in range(200):
        if wickets >= 10 or gamewon:
            break


        bowler = select_bowler_test(bowling_team, bowled_overs, over, bowler, bowling_stats)
        #print(f"\nOver {over + 1}: {bowler.name} bowling")
        message = ""
        over_runs, over_wickets = 0, 0
        
        for ball in range(6):
            if wickets >= 10 or gamewon:
                break

            batting_stats[striker.name]["balls"] += 1
            aggression = 1
            run, out, comments, pace = simulate_ball_test(striker, bowler, venue, settled_meters[striker.name], over, aggression)
            #print(f"{over}.{ball+1} {bowler.name} to {striker.name} | {run} Runs. | {pace} {random.choice(comments)} |{score}/{wickets}")
            striker.match_fatigue += 10/bowler.fitness
            if run < 4: 
                striker.match_fatigue += run * 20/bowler.fitness
                non_striker.match_fatigue += run * 20/bowler.fitness
            
            
            if out:
                wickets += 1
                batting_stats[striker.name]["out"] = True
                bowling_stats[bowler.name]["wickets"] += 1
                if batsman_index < len(batting_team.players):
                    striker = batting_team.players[batsman_index]
                    settled_meters[striker.name] = 0
                    batsman_index += 1
            else:
                score += run
                batting_stats[striker.name]["runs"] += run
                if target and score > target:
                    gamewon = True
                if settled_meters[striker.name] < 50:
                    settled_meters[striker.name] += run * 0.3 + 0.35
                if run % 2 == 1:
                    striker, non_striker = non_striker, striker
            
            over_runs += run
            if out: 
                message += f"{over}.{ball+1} {bowler.name} to {striker.name}: OUT! Score {score}/{wickets}\n"
            else:
                message += f"{over}.{ball+1} {bowler.name} to {striker.name}: {run} Runs. Score {score}/{wickets}\n"
        
        striker, non_striker = non_striker, striker
        bowling_stats[bowler.name]["overs"] += 1
        bowling_stats[bowler.name]["runs"] += over_runs

        message += f"End of Over {over} | Score {score}/{wickets} | {striker.name}:{batting_stats[striker.name]["runs"]}* of {batting_stats[striker.name]["balls"]} | {non_striker.name}:{batting_stats[non_striker.name]["runs"]} of {batting_stats[non_striker.name]["balls"]} | {bowler.name} :  {bowling_stats[bowler.name]["overs"]}-{bowling_stats[bowler.name]["runs"]}-{bowling_stats[bowler.name]["wickets"]}"
        bowled_overs[bowler.name] = bowled_overs.get(bowler.name, 0) + 1
    
    return score, wickets, batting_stats, bowling_stats


import plotly.graph_objects as go
from plotly.subplots import make_subplots


import pandas as pd
import scipy.stats as stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def run_simulation_analysis(num_simulations=20, match_format="t20"):
    # Load data
    players = read_cricketers("data/players.csv")
    teams = read_teams("data/teams.csv", players)
    grounds = read_grounds("data/venues.csv")
    
    print(f"Running {num_simulations} {match_format.upper()} match simulations")
    
    # Initialize data collection
    match_results = []
    batting_stats = {"total_runs": [], "innings_scores": [], "wickets_lost": [], "batter_scores": []}
    player_performances = {"batting": {}, "bowling": {}}
    
    player_data = {"batting": [], "bowling": []}
    player_attributes = {p.name: p for team in teams for p in team.players}
    
    # Run simulations
    for i in range(num_simulations):
        team1, team2 = random.sample(teams, 2)
        venue = random.choice(grounds)
        print(f"Simulation {i+1}/{num_simulations}: {team1.name} vs {team2.name} at {venue.name}")
        
        for player in team1.players + team2.players:
            player.set_match_fitness()
        
        if match_format.lower() == "t20":
            t1_s, t1_w, t1_bat, t1_bowl = simulate_t20_innings(team1, team2, venue)
            t2_s, t2_w, t2_bat, t2_bowl = simulate_t20_innings(team2, team1, venue, t1_s)
        elif match_format.lower() == "odi":
            t1_s, t1_w, t1_bat, t1_bowl = simulate_odi_innings(team1, team2, venue)
            t2_s, t2_w, t2_bat, t2_bowl = simulate_odi_innings(team2, team1, venue, t1_s)
        else:  # test
            t1_s, t1_w, t1_bat, t1_bowl = simulate_test_innings(team1, team2, venue)
            t2_s, t2_w, t2_bat, t2_bowl = simulate_test_innings(team2, team1, venue, t1_s)
        
        match_results.append({
            "team1_name": team1.name, "team1_score": t1_s, "team1_wickets": t1_w,
            "team2_name": team2.name, "team2_score": t2_s, "team2_wickets": t2_w,
            "winner": team1.name if t1_s > t2_s else team2.name
        })
        
        batting_stats["total_runs"].append(t1_s + t2_s)
        batting_stats["innings_scores"].extend([t1_s, t2_s])
        batting_stats["wickets_lost"].extend([t1_w, t2_w])
        
        def update_performance(stats, team_name, bat_or_bowl, perf_list):
            for player_name, stat in stats.items():
                if player_name not in player_performances[bat_or_bowl]:
                    player_performances[bat_or_bowl][player_name] = {
                        "team": team_name,
                        "runs": 0, "balls": 0, "innings": 0, "outs": 0
                    } if bat_or_bowl == "batting" else {
                        "team": team_name, "overs": 0, "runs": 0, "wickets": 0
                    }
                p = player_performances[bat_or_bowl][player_name]
                player_obj = player_attributes[player_name]
                
                if bat_or_bowl == "batting" and stat["balls"] > 0:
                    p["runs"] += stat["runs"]
                    p["balls"] += stat["balls"]
                    p["innings"] += 1
                    p["outs"] += 1 if stat["out"] else 0
                    batting_stats["batter_scores"].append(stat["runs"])
                    perf_list.append({
                        "name": player_name,
                        "runs": stat["runs"],
                        "balls": stat["balls"],
                        "out": stat["out"],
                        "batting_fast": player_obj.batting_fast,
                        "batting_swing": player_obj.batting_swing,
                        "batting_bounce": player_obj.batting_bounce,
                        "batting_spin": player_obj.batting_spin,
                        "batting_rotation": player_obj.batting_rotation,
                        "fitness": player_obj.fitness,
                        "format_avg": player_obj.t20_ave if match_format == "t20" else player_obj.odi_ave if match_format == "odi" else player_obj.test_ave,
                        "format_sr": player_obj.t20_sr if match_format == "t20" else player_obj.odi_sr if match_format == "odi" else player_obj.test_sr
                    })
                elif bat_or_bowl == "bowling" and stat["overs"] > 0:
                    p["overs"] += stat["overs"]
                    p["runs"] += stat["runs"]
                    p["wickets"] += stat["wickets"]
                    perf_list.append({
                        "name": player_name,
                        "overs": stat["overs"],
                        "runs": stat["runs"],
                        "wickets": stat["wickets"],
                        "bowling_pace": player_obj.bowling_pace,
                        "bowling_swing": getattr(player_obj, "bowling_swing", 0),
                        "bowling_bounce": player_obj.bowling_bounce,
                        "bowling_turn": player_obj.bowling_turn,
                        "bowling_control": player_obj.bowling_control,
                        "fitness": player_obj.fitness
                    })
        
        update_performance(t1_bat, team1.name, "batting", player_data["batting"])
        update_performance(t2_bat, team2.name, "batting", player_data["batting"])
        update_performance(t1_bowl, team1.name, "bowling", player_data["bowling"])
        update_performance(t2_bowl, team2.name, "bowling", player_data["bowling"])
    
    # Convert to DataFrames
    batting_df = pd.DataFrame(player_data["batting"])
    bowling_df = pd.DataFrame(player_data["bowling"])
    
    # Calculate key metrics
    batting_df["strike_rate"] = (batting_df["runs"] / batting_df["balls"]) * 100
    bowling_df["economy"] = bowling_df["runs"] / bowling_df["overs"]
    bowling_df["strike_rate"] = (bowling_df["overs"] * 6) / bowling_df["wickets"].replace(0, float('inf'))
    
    # Regression analysis
    batting_attrs = ["batting_fast", "batting_swing", "batting_bounce", "batting_spin", "batting_rotation", "fitness", "format_avg", "format_sr"]
    bowling_attrs = ["bowling_pace", "bowling_swing", "bowling_bounce", "bowling_turn", "bowling_control", "fitness"]
    
    # Batting regression (predict runs)
    X_batting = batting_df[batting_attrs]
    y_batting = batting_df["runs"]
    batting_model = LinearRegression()
    batting_model.fit(X_batting, y_batting)
    batting_coefs = dict(zip(batting_attrs, batting_model.coef_))
    
    # Bowling regression (predict wickets)
    X_bowling_wickets = bowling_df[bowling_attrs]
    y_bowling_wickets = bowling_df["wickets"]
    bowling_wickets_model = LinearRegression()
    bowling_wickets_model.fit(X_bowling_wickets, y_bowling_wickets)
    bowling_wickets_coefs = dict(zip(bowling_attrs, bowling_wickets_model.coef_))
    
    # Bowling regression (predict runs conceded)
    y_bowling_runs = bowling_df["runs"]
    bowling_runs_model = LinearRegression()
    bowling_runs_model.fit(X_bowling_wickets, y_bowling_runs)
    bowling_runs_coefs = dict(zip(bowling_attrs, bowling_runs_model.coef_))
    
    # Standardize coefficients for comparison (optional, scales by standard deviation)
    X_batting_std = X_batting.std()
    batting_coefs_std = {attr: coef * X_batting_std[attr] for attr, coef in batting_coefs.items()}
    X_bowling_std = X_bowling_wickets.std()
    bowling_wickets_coefs_std = {attr: coef * X_bowling_std[attr] for attr, coef in bowling_wickets_coefs.items()}
    bowling_runs_coefs_std = {attr: coef * X_bowling_std[attr] for attr, coef in bowling_runs_coefs.items()}
    
    # Display coefficients
    print(f"\nBatting Stat Coefficients for Runs Scored ({match_format.upper()}):")
    for attr, coef in batting_coefs_std.items():
        print(f"{attr}: {coef:.3f}")
    
    print(f"\nBowling Stat Coefficients for Runs Conceded ({match_format.upper()}):")
    for attr, coef in bowling_runs_coefs_std.items():
        print(f"{attr}: {coef:.3f}")
    
    print(f"\nBowling Stat Coefficients for Wickets Taken ({match_format.upper()}):")
    for attr, coef in bowling_wickets_coefs_std.items():
        print(f"{attr}: {coef:.3f}")
    
    # Plot coefficients
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Batting Stat Impact on Runs", "Bowling Stat Impact on Wickets"))
    
    fig.add_trace(
        go.Bar(x=list(batting_coefs_std.keys()), y=list(batting_coefs_std.values()), name="Batting (Runs)"),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(x=list(bowling_wickets_coefs_std.keys()), y=list(bowling_wickets_coefs_std.values()), name="Bowling (Wickets)"),
        row=1, col=2
    )
    
    fig.update_layout(title_text=f"Stat Impact Analysis ({match_format.upper()})", height=500, width=1000, showlegend=False)
    fig.update_yaxes(title_text="Standardized Coefficient", row=1, col=1)
    fig.update_yaxes(title_text="Standardized Coefficient", row=1, col=2)
    fig.show()


def create_player_performance_plots(player_performances, match_format):
    """
    Create two Plotly scatter plots for batting and bowling performances.
    """
    # Prepare batting data
    batting_data = []
    for player_name, stats in player_performances["batting"].items():
        if stats["innings"] > 0:  # Only include players with at least one innings
            avg = stats["runs"] / stats["innings"] if stats["innings"] > 0 else 0
            sr = (stats["runs"] / stats["balls"]) * 100 if stats["balls"] > 0 else 0
            batting_data.append({
                "name": player_name,
                "team": stats["team"],
                "avg": avg,
                "sr": sr,
                "runs": stats["runs"]
            })
    
    # Prepare bowling data
    bowling_data = []
    for player_name, stats in player_performances["bowling"].items():
        if stats["overs"] > 0:  # Only include players who bowled
            economy = stats["runs"] / stats["overs"] if stats["overs"] > 0 else 0
            strike_rate = (stats["overs"] * 6) / stats["wickets"] if stats["wickets"] > 0 else float('inf')
            bowling_data.append({
                "name": player_name,
                "team": stats["team"],
                "economy": economy,
                "strike_rate": strike_rate,
                "wickets": stats["wickets"]
            })
    
    # Create subplots
    fig = make_subplots(rows=1, cols=2, 
                        subplot_titles=(f"Batting: Avg vs SR ({match_format.upper()})", 
                                       f"Bowling: Economy vs SR ({match_format.upper()})"),
                        horizontal_spacing=0.15)
    
    # Batting scatter plot
    teams = list(set([d["team"] for d in batting_data]))
    for team in teams:
        team_data = [d for d in batting_data if d["team"] == team]
        fig.add_trace(
            go.Scatter(
                x=[d["avg"] for d in team_data],
                y=[d["sr"] for d in team_data],
                text=[d["name"] for d in team_data],
                mode="markers",
                name=team,
                marker=dict(
                    size=[min(d["runs"] / 10, 50) for d in team_data],  # Cap size at 50
                    sizemode="area",
                    sizeref=0.1
                ),
                hovertemplate="%{text}<br>Avg: %{x:.1f}<br>SR: %{y:.1f}<br>Runs: %{customdata}",
                customdata=[d["runs"] for d in team_data]
            ),
            row=1, col=1
        )
    
    # Bowling scatter plot
    for team in teams:
        team_data = [d for d in bowling_data if d["team"] == team]
        fig.add_trace(
            go.Scatter(
                x=[d["economy"] for d in team_data],
                y=[d["strike_rate"] for d in team_data],
                text=[d["name"] for d in team_data],
                mode="markers",
                name=team,
                marker=dict(
                    size=[min(d["wickets"] * 5, 50) for d in team_data],  # Cap size at 50
                    sizemode="area",
                    sizeref=0.1
                ),
                hovertemplate="%{text}<br>Econ: %{x:.1f}<br>SR: %{y:.1f}<br>Wickets: %{customdata}",
                customdata=[d["wickets"] for d in team_data],
                showlegend=False  # Avoid duplicating legend
            ),
            row=1, col=2
        )
    
    # Update layout
    fig.update_layout(
        title_text=f"Player Performance Analysis ({match_format.upper()})",
        height=600,
        width=1200,
        showlegend=True
    )
    fig.update_xaxes(title_text="Batting Average", row=1, col=1)
    fig.update_yaxes(title_text="Strike Rate", row=1, col=1)
    fig.update_xaxes(title_text="Economy Rate", row=1, col=2)
    fig.update_yaxes(title_text="Bowling Strike Rate", row=1, col=2)
    
    # Show the plot
    fig.show()


def create_score_histogram_batter(scores, match_format, bins=None):
    """Create and print a histogram of scores (modified to accept custom bins)."""
    # Use custom bins if provided, otherwise use default based on match format
    if bins is None:
        if match_format == "t20":
            bins = [0, 100, 125, 150, 175, 200, 225, 250]
        elif match_format == "odi":
            bins = [0, 150, 200, 250, 300, 350, 400, 450]
        else:  # test
            bins = [0, 100, 200, 300, 400, 500, 600, 700]
    
    # Count scores in each bin
    bin_counts = [0] * (len(bins) - 1)
    for score in scores:
        for i in range(len(bins) - 1):
            if bins[i] <= score < bins[i+1]:
                bin_counts[i] += 1
                break
    
    # Create ASCII histogram
    max_count = max(bin_counts) if bin_counts else 0
    scale = 40 / max_count if max_count > 0 else 1
    
    print(f"\nIndividual Batter Score Distribution ({match_format.upper()}):")
    for i in range(len(bins) - 1):
        label = f"{bins[i]}-{bins[i+1]-1}"
        bar = "#" * int(bin_counts[i] * scale)
        print(f"{label:10} | {bar} {bin_counts[i]}")

def display_simulation_results(match_results, batting_stats, bowling_stats, player_performances, match_format):
    """Display summary statistics from the simulations."""
    # Calculate match statistics
    total_matches = len(match_results)
    team_wins = {}
    for result in match_results:
        winner = result["winner"]
        team_wins[winner] = team_wins.get(winner, 0) + 1
    
    # Format message
    message = f"\n==== Simulation Results Summary ({match_format.upper()}) ====\n"
    
    # Match outcomes
    message += "\nMatch Outcomes:\n"
    for team, wins in team_wins.items():
        message += f"{team}: {wins} wins ({wins/total_matches*100:.1f}%)\n"
    
    # Batting statistics
    message += "\nBatting Statistics:\n"
    message += f"Average total match runs: {sum(batting_stats['total_runs'])/len(batting_stats['total_runs']):.1f}\n"
    message += f"Average innings score: {sum(batting_stats['innings_scores'])/len(batting_stats['innings_scores']):.1f}\n"
    message += f"Average wickets per innings: {sum(batting_stats['wickets_lost'])/len(batting_stats['wickets_lost']):.1f}\n"
    
    # Distribution of innings scores
    scores = batting_stats['innings_scores']
    score_ranges = {
        "0-99": len([s for s in scores if s < 100]),
        "100-149": len([s for s in scores if 100 <= s < 150]),
        "150-199": len([s for s in scores if 150 <= s < 200]),
        "200+": len([s for s in scores if s >= 200])
    }
    
    message += "\nScore Distribution:\n"
    for range_name, count in score_ranges.items():
        message += f"{range_name}: {count} innings ({count/len(scores)*100:.1f}%)\n"
    
    # Analysis recommendations
    message += "\nRecommendations for Fine-tuning:\n"
    
    avg_score = sum(batting_stats['innings_scores'])/len(batting_stats['innings_scores'])
    if match_format == "t20" and avg_score < 140:
        message += "- T20 scores appear low. Consider increasing batting aggression or reducing bowling effectiveness.\n"
    elif match_format == "t20" and avg_score > 180:
        message += "- T20 scores appear high. Consider decreasing batting aggression or increasing bowling effectiveness.\n"
    
    if match_format == "odi" and avg_score < 240:
        message += "- ODI scores appear low. Consider increasing batting aggression or reducing bowling effectiveness.\n"
    elif match_format == "odi" and avg_score > 320:
        message += "- ODI scores appear high. Consider decreasing batting aggression or increasing bowling effectiveness.\n"
    
    avg_wickets = sum(batting_stats['wickets_lost'])/len(batting_stats['wickets_lost'])
    if avg_wickets < 6:
        message += "- Not enough wickets are falling. Consider increasing bowling effectiveness.\n"
    elif avg_wickets > 9:
        message += "- Too many wickets are falling. Consider reducing bowling effectiveness or increasing batting defense.\n"
    
    print(message)

    # Create histogram of innings scores
    if len(batting_stats['innings_scores']) > 0:
        create_score_histogram(batting_stats['innings_scores'], match_format)

def create_score_histogram(scores, match_format):
    """Create and print a histogram of innings scores."""
    # Determine bins based on match format
    if match_format == "t20":
        bins = [0, 100, 125, 150, 175, 200, 225, 250]
    elif match_format == "odi":
        bins = [0, 150, 200, 250, 300, 350, 400, 450]
    else:  # test
        bins = [0, 100, 200, 300, 400, 500, 600, 700]
    
    # Count scores in each bin
    bin_counts = [0] * (len(bins) - 1)
    for score in scores:
        for i in range(len(bins) - 1):
            if bins[i] <= score < bins[i+1]:
                bin_counts[i] += 1
                break
    
    # Create ASCII histogram
    max_count = max(bin_counts) if bin_counts else 0
    scale = 40 / max_count if max_count > 0 else 1
    
    print(f"\nInnings Score Distribution ({match_format.upper()}):")
    for i in range(len(bins) - 1):
        label = f"{bins[i]}-{bins[i+1]-1}"
        bar = "#" * int(bin_counts[i] * scale)
        print(f"{label:10} | {bar} {bin_counts[i]}")


def collect_ball_data(match_format="t20", num_balls=100000000):
    """
    Collect and analyze individual ball data to fine-tune the simulate_ball methods.
    
    Args:
        match_format: The match format to analyze ("t20", "odi", "test")
        num_balls: Number of ball simulations to run
    """
    players = read_cricketers("data/players.csv")
    teams = read_teams("data/teams.csv", players)
    grounds = read_grounds("data/venues.csv")
    

    
    print(f"Analyzing {num_balls} balls for {match_format} format")
    
    # Result tracking
    results = {
        "runs": [],
        "wickets": 0,
        "dot_balls": 0,
        "boundaries": {"fours": 0, "sixes": 0},
        "run_distribution": {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 6: 0},
        "pace_distribution": [],
        "runs_by_aggression": {},
        "wickets_by_aggression": {},
        "runs_by_settle": {},
        "wickets_by_settle": {}
    }
    
    # Run ball simulations
    for i in range(num_balls):

            # Select random players and venue
        batting_team = random.choice(teams)
        bowling_team = random.choice([t for t in teams if t != batting_team])
        venue = random.choice(grounds)
        
        batsmen = batting_team.players[:6]  # Top 6 batsmen
        bowlers = bowling_team.players[-4:]  # Decent bowlers
        
        # Select random batsman and bowler
        batsman = random.choice(batsmen)
        bowler = random.choice(bowlers)
        
        # Randomize game situation
        over = random.randint(0, 19 if match_format == "t20" else 49)
        settle_meter = random.uniform(0, 100)
        aggression = random.uniform(0.5, 2.0)
        
        # Simulate the ball based on format
        if match_format == "t20":
            run, out, _, pace = simulate_ball_t20(batsman, bowler, venue, settle_meter, over, aggression)
        elif match_format == "odi":
            run, out, _, pace = simulate_ball_odi(batsman, bowler, venue, settle_meter, over, aggression)
        else:  # test
            run, out, _, pace = simulate_ball_test(batsman, bowler, venue, settle_meter, over, aggression)
        
        # Record results
        results["runs"].append(run)
        results["pace_distribution"].append(pace)
        
        # Track run distribution
        results["run_distribution"][run if run in [0, 1, 2, 3, 4, 6] else 0] += 1
        
        if out:
            results["wickets"] += 1
        if run == 0 and not out:
            results["dot_balls"] += 1
        if run == 4:
            results["boundaries"]["fours"] += 1
        if run == 6:
            results["boundaries"]["sixes"] += 1
        
        # Track by aggression (rounded to nearest 0.1)
        agg_key = round(aggression * 10) / 10
        if agg_key not in results["runs_by_aggression"]:
            results["runs_by_aggression"][agg_key] = []
            results["wickets_by_aggression"][agg_key] = 0
        results["runs_by_aggression"][agg_key].append(run)
        if out:
            results["wickets_by_aggression"][agg_key] += 1
        
        # Track by settle meter (in buckets of 10)
        settle_key = int(settle_meter / 10) * 10
        if settle_key not in results["runs_by_settle"]:
            results["runs_by_settle"][settle_key] = []
            results["wickets_by_settle"][settle_key] = 0
        results["runs_by_settle"][settle_key].append(run)
        if out:
            results["wickets_by_settle"][settle_key] += 1
    
    # Display results
    analyze_ball_data_results(results, match_format, num_balls)

def analyze_ball_data_results(results, match_format, num_balls):
    """Analyze and display ball simulation results."""
    print(f"\n==== Ball-by-Ball Analysis ({match_format.upper()}) ====")
    
    # Basic statistics
    total_runs = sum(results["runs"])
    run_rate = total_runs / (num_balls/6)
    dot_percentage = (results["dot_balls"] / num_balls) * 100
    boundary_percentage = ((results["boundaries"]["fours"] + results["boundaries"]["sixes"]) / num_balls) * 100
    
    print(f"\nBasic Statistics:")
    print(f"Total runs: {total_runs}")
    print(f"Run rate: {run_rate:.2f}")
    print(f"Total wickets: {results['wickets']}")
    print(f"Wickets per over: {(results['wickets'] / (num_balls/6)):.2f}")
    print(f"Dot ball percentage: {dot_percentage:.1f}%")
    print(f"Boundary percentage: {boundary_percentage:.1f}%")
    
    # Run distribution
    print("\nRun Distribution:")
    for run, count in results["run_distribution"].items():
        percentage = (count / num_balls) * 100
        bar = "#" * int(percentage/2)
        print(f"{run} runs: {percentage:.1f}% {bar} ({count})")
    
    # Aggression analysis
    print("\nRuns by Aggression Level:")
    for agg, runs in sorted(results["runs_by_aggression"].items()):
        avg_run = sum(runs) / len(runs) if runs else 0
        wickets = results["wickets_by_aggression"][agg]
        wicket_rate = (wickets / len(runs)) * 100 if runs else 0
        print(f"Aggression {agg:.1f}: Avg runs {avg_run:.2f}, Wicket rate {wicket_rate:.1f}%")
    
    # Settle meter analysis
    print("\nPerformance by Settle Meter:")
    for settle, runs in sorted(results["runs_by_settle"].items()):
        avg_run = sum(runs) / len(runs) if runs else 0
        wickets = results["wickets_by_settle"][settle]
        wicket_rate = (wickets / len(runs)) * 100 if runs else 0
        print(f"Settle {settle}-{settle+9}: Avg runs {avg_run:.2f}, Wicket rate {wicket_rate:.1f}%")
    
    # Recommendations based on format
    print("\nRecommendations:")
    if match_format == "t20":
        if run_rate < 7.5:
            print("- T20 run rate is too low. Consider increasing batting effectiveness.")
        elif run_rate > 9.5:
            print("- T20 run rate is too high. Consider decreasing batting effectiveness.")
        
        if dot_percentage < 30:
            print("- T20 dot ball percentage is low. Consider increasing bowler dominance.")
        elif dot_percentage > 50:
            print("- T20 dot ball percentage is high. Consider decreasing bowler dominance.")
        
        if boundary_percentage < 15:
            print("- T20 boundary percentage is low. Consider boosting boundaries.")
        elif boundary_percentage > 25:
            print("- T20 boundary percentage is high. Consider reducing boundaries.")
    
    elif match_format == "odi":
        if run_rate < 5:
            print("- ODI run rate is too low. Consider increasing batting effectiveness.")
        elif run_rate > 7:
            print("- ODI run rate is too high. Consider decreasing batting effectiveness.")
        
        # Similar recommendations for ODI format
    
    else:  # test
        if run_rate < 3:
            print("- Test run rate is too low. Consider increasing batting effectiveness.")
        elif run_rate > 4:
            print("- Test run rate is too high. Consider decreasing batting effectiveness.")
        
        # Similar recommendations for Test format

def play_ashes(n): 
    wins = 0
    for i in range(n): 
        if play_match("AUS","ENG","Perth","test") == "ENG": 
            wins += 1
        if play_match("AUS","ENG","SCG","test") == "ENG": 
            wins += 1
        if play_match("AUS","ENG","Brisbane","test") == "ENG": 
            wins += 1
        if play_match("AUS","ENG","MCG","test") == "ENG": 
            wins += 1
        if play_match("AUS","ENG","Gabba","test") == "ENG": 
            wins += 1
    print (wins/(n*5))
# Run the bot


# For analyzing multiple match simulations
# run_simulation_analysis(num_simulations=100, match_format="test")
run_simulation_analysis(num_simulations=1000, match_format="test")
