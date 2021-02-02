from grib_loader import GRIBLoader
from util import angle360
from wind.wind import Wind


class GRIBWind(Wind):
    def __init__(self):
        self.loader = GRIBLoader(path='./tmp')

    def get_wind(self, loc, h, t):
        direction, velocity = self.loader.get_wind(t, loc)
        return angle360(h - direction), velocity  # direction, speed

