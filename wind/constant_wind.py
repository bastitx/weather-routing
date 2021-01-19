from util import angle360
from wind.wind import Wind


class ConstantWind(Wind):
    def __init__(self, direction, velocity):
        self.direction = direction
        self.velocity = velocity

    def get_wind(self, loc, h, t):
        return angle360(h - self.direction), self.velocity  # direction, speed
