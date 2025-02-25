# models/player.py

class Player:
    def __init__(self, name, role, 
                 batting_defense, batting_rotation, batting_boundary, batting_power,
                 batting_spin, batting_fast, batting_swing, batting_bounce, test_ave, odi_ave, t20_ave, test_sr, odi_sr, t20_sr,
                 bowling_type, bowling_bounce, bowling_seam, bowling_swing,
                 bowling_pace, bowling_control, bowling_turn, bowling_variations,
                 age, fitness, fatigue, strain, form, followers, marketability, 
                 injury_status, prevmatch=None):

        self.name = name  # Player Name
        self.role = role  # Batsman, Bowler, All-rounder, Wicketkeeper

        # Batting attributes
        self.batting_defense = batting_defense  # Defensive ability
        self.batting_rotation = batting_rotation  # Ability to rotate strike
        self.batting_boundary = batting_boundary  # Ability to hit boundaries
        self.batting_power = batting_power  # Ability to hit sixes
        self.batting_spin = batting_spin  # Bonus against spin bowling
        self.batting_fast = batting_fast  # Bonus against fast bowling
        self.batting_swing = batting_swing  # Bonus against swinging deliveries
        self.batting_bounce = batting_bounce  # Bonus against bouncing deliveries
        self.test_ave = test_ave
        self.odi_ave = odi_ave
        self.t20_ave = t20_ave
        self.test_sr = test_sr
        self.odi_sr = odi_sr 
        self.t20_sr = t20_sr

        # Bowling attributes
        self.bowling_type = bowling_type  # Spin or Pace
        self.bowling_bounce = bowling_bounce  # Effectiveness on bouncy pitches
        self.bowling_seam = bowling_seam  # Amount of seam movement for pacers
        self.bowling_swing = bowling_swing  # Amount of swing for pacers
        self.bowling_pace = bowling_pace  # Average bowling speed
        self.bowling_control = bowling_control  # Lower control = more bad deliveries
        self.bowling_turn = bowling_turn  # Degrees of turn for spinners
        self.bowling_variations = bowling_variations  # Effectiveness of variations for spinners

        # Physical and form attributes
        self.age = age  # Affects stat progression
        self.fitness = fitness  # Determines fatigue resistance & aging effects
        self.fatigue = fatigue  # Fatigue level; affects performance
        self.strain = strain  # Lasting physical toll from playing with high fatigue
        self.form = form  # Current form (affects performance)
        self.match_fatigue = 0

        # Popularity & injury status
        self.followers = followers  # Social media following
        self.marketability = marketability  # Determines how fast followers grow
        self.injury_status = injury_status  # Current injury status
        self.prevmatch = prevmatch  # Date of last match played

    def set_match_fitness(self):
        self.match_fatigue = max(self.fatigue-20,0)

    def __repr__(self):
        return f"<Player {self.name} ({self.role}) - Form: {self.form}>"
