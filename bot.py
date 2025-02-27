import discord
from discord.ext import commands
from utils.csvreader import read_cricketers, read_teams, read_grounds
from models.player import Player
from models.team import Team
from models.venue import Stadium
import math
import asyncio
from loc import simulate_ball_odi, calculate_aggression_odi, simulate_ball_test, select_bowler_test, get_ball_probabilities, select_bowler_t20, simulate_ball_t20, calculate_aggression_t20
import random

# Load data from CSV files
players = read_cricketers('data/players.csv')
teams = read_teams('data/teams.csv', players)
grounds = read_grounds('data/venues.csv')


# Set up the bot with a command prefix
# Create an instance of Intents
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent

# Initialize the bot with the intents
bot = commands.Bot(command_prefix="!", intents=intents)

import math
def calculate_revenue(match_format, fanbase_team1, fanbase_team2, player_followers, 
                      tournament_profile, closeness, runs_scored, stadium_quality, stadium_capacity):
    """
    Calculate cricket match revenue split by ticket sales and broadcast rights.

    This model combines several factors:
      - Fan base: The combined fan following of both teams.
      - Player popularity: Sum of individual players' Instagram followers.
      - Tournament profile: A rating (1 to 5) indicating the tournament's importance.
      - Match competitiveness (closeness): A value between 0 and 1; a closer match tends to boost both ticket and broadcast interest.
      - Runs scored: A proxy for match excitement (more runs can indicate a thrilling game).
      - Format multipliers: Different match formats affect revenue differently.
      - Stadium factors: Quality (1 to 10) and capacity directly influence ticket revenue.

    The function uses arbitrary scaling constants to blend these factors into two revenue streams:
      - Broadcast revenue is largely driven by the overall fan base, player popularity, tournament importance,
        and enhanced by competitive, high-scoring games.
      - Ticket revenue is driven by stadium capacity, adjusted by stadium quality, match competitiveness,
        tournament profile, and the match format.

    Args:
        match_format (str): Match format ('T20', 'ODI', 'Test').
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

    # --- Format Multipliers ---
    # These factors adjust revenue based on the match format.
    if match_format == 'T20':
        format_broadcast_factor = 1.3  # T20 games are fast-paced and attract high broadcast interest.
        format_ticket_factor = 1.1
    elif match_format == 'ODI':
        format_broadcast_factor = 0.7
        format_ticket_factor = 0.8  # ODI games often draw larger live crowds.
    elif match_format == 'Test':
        format_broadcast_factor = 1  # Longer format; broadcast interest is typically lower.
        format_ticket_factor = 0.8
    else:
        # Default multipliers if the format is unrecognized.
        format_broadcast_factor = 1.0
        format_ticket_factor = 1.0

    # --- Fan Base and Player Popularity ---
    # Convert fan base and player follower counts from millions to actual numbers.
    total_fanbase = (fanbase_team1 + fanbase_team2) 
    total_player_followers = player_followers 

    # Baseline broadcast revenue is influenced by the fan base and enhanced by player popularity.
    # Here, we assume a base contribution of $0.20 per fan and a bonus of $0.10 per follower.
    broadcast_base = total_fanbase * 0.2
    popularity_bonus = total_player_followers * 0.1
    base_broadcast_revenue = broadcast_base + popularity_bonus

    # --- Multipliers for Match Excitement ---
    # Closeness increases viewer interest; a perfectly competitive match (closeness = 1) doubles the effect.
    closeness_multiplier = 1 + closeness

    # Runs scored add a modest boost; for instance, every 1000 runs increases revenue by 100%.
    runs_multiplier = 1 + (runs_scored / 1000)

    # --- Final Broadcast Revenue Calculation ---
    # Tournament profile and format further amplify the base revenue.
    broadcast_revenue = (base_broadcast_revenue * tournament_profile *
                         format_broadcast_factor * closeness_multiplier * runs_multiplier)

    # --- Ticket Revenue Calculation ---
    # Determine average ticket price, using stadium quality as an adjustment.
    # A quality rating of 5 corresponds to a baseline price of $50.
    average_ticket_price = 50 * (stadium_quality / 5)

    # Base ticket revenue from stadium capacity.
    ticket_base = stadium_capacity * average_ticket_price

    # Demand for tickets is boosted by both the competitiveness and the tournament profile.
    # The tournament profile is normalized by dividing by 3 (mid-scale of 1 to 5).
    ticket_multiplier = (1 + closeness) * (tournament_profile / 3)

    # Final ticket revenue calculation incorporates the match format and runs scored factors.
    ticket_revenue = broadcast_revenue * (stadium_quality / 30) * capacity / 200000

    return int(broadcast_revenue/10), ticket_revenue    

async def simulate_test(ctx, team1, team2, venue):
    """Simulate a Test match between two teams, including follow-ons."""
    import random  # Ensure random is imported

    # Toss: randomly decide who bats first
    if random.randint(1, 100) > 50:
        team1, team2 = team2, team1

    pitch = venue

    # First innings for team1
    team1_score1, team1_wickets1, team1_batting_stats1, team1_bowling_stats1 = await simulate_test_innings(ctx, team1, team2, pitch)
    await display_scorecard_discord(ctx, team1.name, team1_batting_stats1, team1_bowling_stats1)

    # First innings for team2
    team2_score1, team2_wickets1, team2_batting_stats1, team2_bowling_stats1 = await simulate_test_innings(ctx, team2, team1, pitch)
    await display_scorecard_discord(ctx, team2.name, team2_batting_stats1, team2_bowling_stats1)

    # Check for follow-on: if team1 leads by 200 or more runs
    if team1_score1 - team2_score1 >= 200:
        await ctx.send(f"{team1.name} enforces the follow-on on {team2.name}!")
        # Team2 bats their second innings (follow-on)
        team2_score2, team2_wickets2, team2_batting_stats2, team2_bowling_stats2 = await simulate_test_innings(ctx, team2, team1, pitch)
        await display_scorecard_discord(ctx, team2.name, team2_batting_stats2, team2_bowling_stats2)

        # Team1 bats in their second innings, chasing a target:
        # Target = (team2 first + team2 second) - team1 first + 1
        target = team2_score1 + team2_score2 - team1_score1 + 1
        await ctx.send(f"{team1.name} needs {target} runs to win in the final innings!")
        team1_score2, team1_wickets2, team1_batting_stats2, team1_bowling_stats2 = await simulate_test_innings(ctx, team1, team2, pitch, target=target)
        await display_scorecard_discord(ctx, team1.name, team1_batting_stats2, team1_bowling_stats2)

        # Decide result based on the final innings
        if team1_score2 >= target:
            wickets_remaining = 10 - team1_wickets2
            await ctx.send(f"{team1.name} wins by {wickets_remaining} wickets!")
        else:
            runs_short = target - team1_score2
            await ctx.send(f"{team2.name} wins by {runs_short} runs!")
    else:
        # No follow-on: team1 bats their second innings
        team1_score2, team1_wickets2, team1_batting_stats2, team1_bowling_stats2 = await simulate_test_innings(ctx, team1, team2, pitch)
        await display_scorecard_discord(ctx, team1.name, team1_batting_stats2, team1_bowling_stats2)

        # Team2 chases in their second innings:
        # Target = (team1 first + team1 second) - team2 first + 1
        target = team1_score1 + team1_score2 - team2_score1 + 1
        await ctx.send(f"{team2.name} needs {target} runs to win in the final innings!")
        team2_score2, team2_wickets2, team2_batting_stats2, team2_bowling_stats2 = await simulate_test_innings(ctx, team2, team1, pitch, target=target)
        await display_scorecard_discord(ctx, team2.name, team2_batting_stats2, team2_bowling_stats2)

        # Decide result based on the final innings
        if team2_score2 >= target:
            wickets_remaining = 10 - team2_wickets2
            await ctx.send(f"{team2.name} wins by {wickets_remaining} wickets!")
        else:
            runs_short = target - team2_score2
            await ctx.send(f"{team1.name} wins by {runs_short} runs!")



async def simulate_test_innings(ctx, batting_team: Team, bowling_team: Team, venue, target=None):
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

    for bowler in bowling_team.players: 
        bowler.match_fatigue = bowler.fatigue
    
    for over in range(200):
        if wickets >= 10 or gamewon:
            break


        bowler = select_bowler_test(bowling_team, bowled_overs, over, bowler, bowling_stats)
        #await ctx.send(f"\nOver {over + 1}: {bowler.name} bowling")

        over_runs, over_wickets = 0, 0
        
        for ball in range(6):
            if wickets >= 10 or gamewon:
                break

            batting_stats[striker.name]["balls"] += 1
            aggression = 1
            run, out, comments, pace = simulate_ball_test(striker, bowler, venue, settled_meters[striker.name], over, aggression)
            if out: 
                await ctx.send(f"{over}.{ball+1} {bowler.name} to {striker.name} | {round(pace,1)} kmph | OUT! | {random.choice(comments)} | {score}/{wickets}")
            elif run > 3:
                await ctx.send(f"{over}.{ball+1} {bowler.name} to {striker.name} | {round(pace,1)} kmph | {run} Runs |  {random.choice(comments)} |{score}/{wickets}")
            striker.match_fatigue += 40/bowler.fitness
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
                    settled_meters[striker.name] += run * 0.3 + 0.4
                if run % 2 == 1:
                    striker, non_striker = non_striker, striker
            
            over_runs += run
        
        striker, non_striker = non_striker, striker
        bowling_stats[bowler.name]["overs"] += 1
        bowling_stats[bowler.name]["runs"] += over_runs

        await ctx.send(f"End of Over {over + 1} | Score {score}/{wickets} | {striker.name}:{batting_stats[striker.name]["runs"]}* of {batting_stats[striker.name]["balls"]} | {non_striker.name}:{batting_stats[non_striker.name]["runs"]} of {batting_stats[non_striker.name]["balls"]} | {bowler.name} :  {bowling_stats[bowler.name]["overs"]}-{bowling_stats[bowler.name]["runs"]}-{bowling_stats[bowler.name]["wickets"]}\n")
        bowled_overs[bowler.name] = bowled_overs.get(bowler.name, 0) + 1

    
    return score, wickets, batting_stats, bowling_stats
        

       
async def display_scorecard(ctx, batting_stats, bowling_stats, team_name, score, wickets):
    """Display the scorecard for a team with enhanced details."""
    

    await ctx.send(f"{team_name} {score}/{wickets}")
    
    await ctx.send("\nBatting:\n")
    await ctx.send("Batter           Runs  Balls  SR\n")
    await ctx.send("-" * 35)
    for player, stats in batting_stats.items():
        if stats['balls'] > 0:  # Only show batsmen who faced deliveries
            strike_rate = (stats['runs'] * 100) / stats['balls']
            status = "*" if not stats['out'] else ""
            await ctx.send(f"\n{player:<15} {stats['runs']}{status:<5} {stats['balls']:<6} {strike_rate:>5.1f}")

    await ctx.send("\nBowling:")
    await ctx.send("Bowler           O    R    W    Econ")
    await ctx.send("-" * 40)
    for player, stats in bowling_stats.items():
        if stats['overs'] > 0:  # Only show bowlers who bowled
            economy = stats['runs'] / stats['overs'] if stats['overs'] > 0 else 0
            await ctx.send(f"{player:<15} {stats['overs']:<4} {stats['runs']:<4} {stats['wickets']:<4} {economy:>5.1f}")



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
            bowler_stats = f"{bowler}: {over_runs}/{over_wickets} ({bowling_stats[bowler]['overs']}-{bowling_stats[bowler]['runs']}-{bowling_stats[bowler]['wickets']})"
            
            print(f"Score: {current_score}/{current_wickets} | {striker_stats}, {non_striker_stats} | {bowler_stats}")
        
    

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


async def display_scorecard_discord(ctx, team_name, batting_stats, bowling_stats):
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
    await ctx.send(batting_card)

    # Create bowling scorecard
    bowling_card = f"**{team_name} Bowling**\n```\n"
    bowling_card += "Bowler          O    M    R    W    Econ\n"
    bowling_card += "-" * 45 + "\n"
    
    for player, stats in bowling_stats.items():
        if stats["overs"] > 0:  # Only show bowlers who bowled
            economy = stats["runs"] / stats["overs"] if stats["overs"] > 0 else 0
            bowling_card += f"{player:<15} {stats['overs']:<4}  {stats['runs']:<4} {stats['wickets']:<4} {economy:.2f}\n"
    
    bowling_card += "```"
    await ctx.send(bowling_card)



async def simulate_t20_innings(ctx, batting_team: Team, bowling_team: Team, venue, target=None):
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
            aggression = calculate_aggression_odi(over, venue, target, striker, non_striker, settled_meters[striker.name], settled_meters[non_striker.name])
            run, out, comments, pace = simulate_ball_t20(striker, bowler, venue, settled_meters[striker.name], over, aggression)
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
                if settled_meters[striker.name] < 50:
                    settled_meters[striker.name] += -0.4 + run*0.8
                if run % 2 == 1:
                    striker, non_striker = non_striker, striker
            
            over_runs += run
            if out: 
                await ctx.send(f"{over}.{ball+1} {bowler.name} to {striker.name} | {round(pace,1)} kmph | OUT! | {random.choice(comments)} | {score}/{wickets}")
            else:
                await ctx.send(f"{over}.{ball+1} {bowler.name} to {striker.name} | {round(pace,1)} kmph | {run} Runs |  {random.choice(comments)} |{score}/{wickets}")
         
        striker, non_striker = non_striker, striker
        bowling_stats[bowler.name]["overs"] += 1
        bowling_stats[bowler.name]["runs"] += over_runs

        await ctx.send(f"End of Over {over} | Score {score}/{wickets} | {striker.name}:{batting_stats[striker.name]["runs"]}* of {batting_stats[striker.name]["balls"]} | {non_striker.name}:{batting_stats[non_striker.name]["runs"]} of {batting_stats[non_striker.name]["balls"]} | {bowler.name} :  {bowling_stats[bowler.name]["overs"]}-{bowling_stats[bowler.name]["runs"]}-{bowling_stats[bowler.name]["wickets"]}")
        bowled_overs[bowler.name] = bowled_overs.get(bowler.name, 0) + 1
    
    return score, wickets, batting_stats, bowling_stats


async def simulate_t20(ctx, team1, team2, venue):
    """Simulate a match between any two teams."""
    # Random toss to decide who bats first
    if random.randint(1, 100) > 50:
        team1, team2 = team2, team1
    
    pitch = venue
    
    # Simulate first innings
    team1_score, team1_wickets, team1_batting_stats, team1_bowling_stats = await simulate_t20_innings(ctx, team1, team2, pitch)
    
    # Display scorecard for team 1
    await display_scorecard_discord(ctx, team1.name, team1_batting_stats, team1_bowling_stats)
    
    # Simulate second innings
    team2_score, team2_wickets, team2_batting_stats, team2_bowling_stats = await simulate_t20_innings(ctx, team2, team1, pitch, team1_score)

    
    # Display scorecard for team 2
    await display_scorecard_discord(ctx, team2.name, team2_batting_stats, team2_bowling_stats)

    # Determine winner
    if team1_score > team2_score:
        await ctx.send(f"\n{team1.name} wins by {team1_score - team2_score} runs!")
    elif team2_score > team1_score:
        await ctx.send(f"\n{team2.name} wins by {10 - team2_wickets} wickets!")
    else:
        await ctx.send("\nMatch tied!")

    
    return (team1_score, team1_wickets, team2_score, team2_wickets)


@bot.command()
@commands.has_role("auctioneer")
async def play_match(ctx, team1name: str, team2name: str, venuename: str, format: str):
    """
    Command to start a match simulation.
    Loads teams, venue, and match format, then calls the match simulation logic.
    """
    await ctx.send(f"Match Between {team1name} & {team2name}")
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
        await ctx.send(f"Team '{team1name}' not found!")
        return
    if not team2:
        await ctx.send(f"Team '{team2name}' not found!")
        return
    if not ground:
        await ctx.send(f"Ground '{venuename}' not found!")
        return
    if format.lower() not in ["test", "odi", "t20"]:
        await ctx.send("Invalname match format! Choose from: Test, ODI, T20.")
        return

    # Confirm match setup
    await ctx.send(f"Starting {format.upper()} match between {team1.name} and {team2.name} at {ground.name}!")

    # Placeholder for match simulation logic
    # TODO: Implement the match simulation logic
    for player in team1.players: 
        player.set_match_fitness()
    for player in team2.players: 
        player.set_match_fitness()
    if format.upper() == "ODI": 
        await simulate_odi(ctx, team1, team2, ground)
    if format.lower() == "test":
        await simulate_test(ctx, team1, team2, ground)
    if format.lower() == "t20":
        await simulate_t20(ctx, team1, team2, ground)




def get_ball_probabilities(expected_runs, striker):
    # Simple but reasonable distribution that can be tuned
    if expected_runs <= 0:
        return [1, 0, 0, 0, 0, 0, 0]  # All dots
    
    # Base probabilities - can be adjusted
    p0 = 0.6  # Dot balls are common
    p1 = 0.21 # Singles are next most common
    p2 = 0.06
    p3 = 0.01
    p4 = 0.08
    p6 = 0.04
    
    # Calculate current expected value
    current_exp = 0*p0 + 1*p1 + 2*p2 + 3*p3 + 4*p4 + 6*p6
    
    # Adjust probabilities to match expected runs
    scale = expected_runs / current_exp if current_exp > 0 else 0
    
    # Scale all non-zero probabilities
    sixmult = (striker.batting_power/70)
    fourmult = (striker.batting_boundary/70)

    p1 *= scale
    p2 *= scale
    p3 *= scale
    p4 *= scale 
    p6 *= scale 
    

    # Put remaining probability into dots
    p0 = 1 - (p1 + p2 + p3 + p4 + p6)
    
    return [p0, p1, p2, p3, p4, 0, p6]  # Note the 0 at index 5


async def simulate_odi(ctx, team1, team2, venue):
    """Simulate a match between any two teams."""
    # Random toss to decide who bats first
    if random.randint(1, 100) > 50:
        team1, team2 = team2, team1
    
    pitch = venue
    
    # Simulate first innings
    team1_score, team1_wickets, team1_batting_stats, team1_bowling_stats = await simulate_odi_innings(ctx, team1, team2, pitch)
    
    # Display scorecard for team 1
    await display_scorecard_discord(ctx, team1_batting_stats, team1_bowling_stats, team1.name, team1_score, team1_wickets)
    
    # Simulate second innings
    team2_score, team2_wickets, team2_batting_stats, team2_bowling_stats = await simulate_odi_innings(ctx, team2, team1, pitch, team1_score)

    
    # Display scorecard for team 2
    await display_scorecard_discord(ctx, team2_batting_stats, team2_bowling_stats, team2.name, team2_score, team2_wickets)

    # Determine winner
    if team1_score > team2_score:
        await ctx.send(f"\n{team1.name} wins by {team1_score - team2_score} runs!")
    elif team2_score > team1_score:
        await ctx.send(f"\n{team2.name} wins by {10 - team2_wickets} wickets!")
    else:
        await ctx.send("\nMatch tied!")

    '''broadcast, tickets = calculate_revenue(
    format='ODI',
    fanbase_team1=team1.fanbase/1000000,
    fanbase_team2=team2.fanbase/1000000,
    player_followers= sum(player.followers for player in team1.players) + sum(player.followers for player in team2.players) / 1000000,
    tournament_profile=4,
    closeness=team1_score/team2_score,
    runs_scored=team1_score + team2_score,
    stadium_quality=venue.quality,
    stadium_capacity=venue.capacity
)
    await ctx.send(f"Total Revenue: {broadcast} + {tickets}" )'''
    return (team1_score, team1_wickets, team2_score, team2_wickets)




async def simulate_odi_innings(ctx, batting_team: Team, bowling_team: Team, venue, target=None):
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
        message = ""
        over_runs, over_wickets = 0, 0
        
        for ball in range(6):
            if wickets >= 10 or gamewon:
                break

            batting_stats[striker.name]["balls"] += 1
            aggression = calculate_aggression_odi(over, venue, target, striker, non_striker, settled_meters[striker.name], settled_meters[non_striker.name])
            run, out, comments, pace = simulate_ball_odi(striker, bowler, venue, settled_meters[striker.name], over, aggression)
            
           
            striker.match_fatigue += 20/striker.fitness
            if run < 4: 
                striker.match_fatigue += run * 40/striker.fitness
                non_striker.match_fatigue += run * 40/non_striker.fitness
            
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
                if settled_meters[striker.name] < 60:
                    settled_meters[striker.name] += run * 0.3 + 0.2
                if run % 2 == 1:
                    striker, non_striker = non_striker, striker
            
            if out: 
                await ctx.send(f"{over}.{ball+1} {bowler.name} to {striker.name} | {round(pace,1)} kmph | OUT! | {random.choice(comments)} | {score}/{wickets}")
            else:
                await ctx.send(f"{over}.{ball+1} {bowler.name} to {striker.name} | {round(pace,1)} kmph | {run} Runs |  {random.choice(comments)} |{score}/{wickets}")
        
            
            over_runs += run
           
        striker, non_striker = non_striker, striker
        bowling_stats[bowler.name]["overs"] += 1
        bowling_stats[bowler.name]["runs"] += over_runs

        message += f"End of Over {over + 1} | Score {score}/{wickets} | {striker.name}:{batting_stats[striker.name]["runs"]}* of {batting_stats[striker.name]["balls"]} | {non_striker.name}:{batting_stats[non_striker.name]["runs"]} of {batting_stats[non_striker.name]["balls"]} | {bowler.name} :  {bowling_stats[bowler.name]["overs"]}-{bowling_stats[bowler.name]["runs"]}-{bowling_stats[bowler.name]["wickets"]}"
        await ctx.send(message)
        bowled_overs[bowler.name] = bowled_overs.get(bowler.name, 0) + 1
    
    return score, wickets, batting_stats, bowling_stats




# Run the bot

bot.run('MTI5ODM3MTAzMjg5MzA5NjAyNw.GXSyZA.y_78Wbzx8ZT4f1e3V5iJBmyDMDE9-XY4rnJDzE')