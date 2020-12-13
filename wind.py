from util import angle360


class Wind:
    def __init__(self, direction, velocity):
        self.direction = direction
        self.velocity = velocity

    def get_wind(self, x, y, h, t):
        return angle360(h - self.direction), self.velocity  # direction, speed
