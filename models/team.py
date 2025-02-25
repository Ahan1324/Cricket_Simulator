class Team:
    def __init__(self, name, players, fanbase):
        """
        Initialize a Team object.

        :param id: int - Unique identifier for the team.
        :param name: str - Team name.
        :param players: list - List of Player objects associated with the team.
        """
        self.name = name
        self.players = players  # List of Player objects
        self.fanbase = fanbase

    def get_average_batting(self):
        """
        Calculate the average batting ability of the team based on all players.
        """
        if not self.players:
            return 0
        total_batting = sum((p.batting_power + p.batting_defense + p.batting_rotation) / 3 for p in self.players)
        return total_batting / len(self.players)

    def get_average_bowling(self):
        """
        Calculate the average bowling ability of the team based on all players.
        """
        if not self.players:
            return 0
        total_bowling = sum((p.bowling_pace + p.bowling_control + p.bowling_turn) / 3 for p in self.players)
        return total_bowling / len(self.players)

    def get_total_followers(self):
        """
        Calculate the total number of followers for the team.
        """
        return sum(p.followers for p in self.players)

    def __str__(self):
        return f"Team {self.name} (ID: {self.id}) - Players: {len(self.players)}"
