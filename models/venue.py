class Stadium:
    def __init__(self, id, name, quality, capacity, pace, turn, bounce, hardness, grass_cover):
        """
        Initialize a Ground object.

        :param id: int - Unique identifier for the ground.
        :param name: str - Name of the cricket ground.
        :param quality: str - Ground quality (Excellent, Good, Fair, etc.).
        :param capacity: int - Number of spectators the ground can hold.
        :param pace: int - Pitch pace rating (0-100).
        :param turn: int - Spin-friendliness of the pitch (0-100).
        :param bounce: int - Bounce level of the pitch (0-100).
        :param hardness: int - Pitch hardness (0-100).
        :param grass_cover: int - Amount of grass on the pitch (0-100).
        """
        self.id = id
        self.name = name
        self.quality = quality
        self.capacity = capacity
        self.pace = pace
        self.turn = turn
        self.bounce = bounce
        self.hardness = hardness
        self.grass_cover = grass_cover

    def is_spin_friendly(self):
        """
        Check if the pitch favors spin bowlers.
        """
        return self.turn > 60 and self.grass_cover < 50

    def is_pace_friendly(self):
        """
        Check if the pitch favors fast bowlers.
        """
        return self.pace > 70 and self.hardness > 60

    def __str__(self):
        return f"{self.name} (Quality: {self.quality}, Capacity: {self.capacity})"
