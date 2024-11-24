score = 0

class ScoreController:
    def __init__(self):
        self._score = 0

    def score_handler(self, added_score: int):
        self._score += added_score

    def reset_score(self):
        self._score = 0

    def get_score(self):
        return self._score