from shapely.geometry import Point

from util import angle360
from wind.wind import Wind
import numpy as np


class Polar:
    def __init__(self, polar):
        self.polar = polar

    def get_speed(self, loc: Point, heading: float, velocity_boat: float, t: int, wind: Wind):
        # TODO: Currently true wind speed; add currents and apparent wind (taking into account speed?)
        # TODO: should polar map from true wind speed to velocity or from apparent wind speed?
        direction_true_wind, velocity_true_wind = wind.get_wind(loc, heading, t)
        # law of cosines
        velocity_apparent_wind = np.sqrt(velocity_boat ** 2 + velocity_true_wind ** 2 +
                                         2 * velocity_boat * velocity_true_wind *
                                         np.cos(np.deg2rad(direction_true_wind)))
        if velocity_apparent_wind == 0:
            direction_apparent_wind = 0.
        elif velocity_boat == 0:
            direction_apparent_wind = direction_true_wind
        else:
            direction_apparent_wind = angle360(np.rad2deg(np.arccos(
                (velocity_apparent_wind ** 2 + velocity_boat ** 2 - velocity_true_wind ** 2) /
                (2 * velocity_apparent_wind * velocity_boat))))
        direction_apparent_wind = angle360(direction_apparent_wind)
        if direction_apparent_wind > 180:
            x = 360 - direction_apparent_wind
        else:
            x = direction_apparent_wind
        return np.interp(x, self.polar[0], self.polar[1])


if __name__ == '__main__':
    from wind.constant_wind import ConstantWind
    # angle in degrees -> speed in m/s TODO: make dependent on wind speed
    p = np.array([[0., 45., 90., 135., 180.], [0., 0., 2.8, 4.2, 2.8]])
    p = Polar(p)
    w = ConstantWind(150., 20.)
    print(p.get_speed(0., 0., 270., 0., 0, w))
