from pyproj import Geod
import numpy as np

from polar import Polar
from routers.gc_router import GCRouter
from routers.isochrone_router import IsochroneRouter
from routing_point import RoutingPoint
from util import angle360
from wind import Wind


class Router:
    def __init__(self, start_point, end_point, polar, wind, crs='WGS84'):
        self.start_point = start_point
        self.end_point = end_point
        self.polar = polar
        self.wind = wind
        self.g = Geod(ellps=crs)

    def calculate_routing(self):
        raise NotImplementedError()

    def get_isochrones(self):
        raise NotImplementedError()


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    import cartopy.crs as crs
    from shapely.geometry import Point, LineString

    start = Point(-4.91519, 48.26118)
    # end = Point(-74.71870, 38.86484)
    end = Point(-60.69365, 14.77645)

    p = np.array([[0., 45., 90., 135., 180.], [0., 0., 2.8, 4.2, 2.8]])
    p = Polar(p)
    w = Wind(150., 20.)

    r = IsochroneRouter(start, end, p, w)
    best_point_iso = r.calculate_routing()
    isochrones = r.get_isochrones()
    r = GCRouter(start, end, p, w)
    best_point_gc = r.calculate_routing(20)
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1, projection=crs.Mercator())
    # ax.set_global()
    ax.coastlines()
    # plt.plot([start.x, end.x], [start.y, end.y], transform=crs.PlateCarree())

    def color(s):
        if s < 2:
            return 'black'
        elif 2 <= s < 3:
            return 'blue'
        elif 3 <= s < 4:
            return 'green'
        else:
            return 'red'
    for p in [best_point_iso, best_point_gc]
        while p.previous_point is not None:
            plt.plot([p.x, p.previous_point.x], [p.y, p.previous_point.y], transform=crs.PlateCarree(), c=color(p.speed))
            p = p.previous_point
    for isochrone in isochrones:
        isochrone = np.array([[x.x, x.y] for x in isochrone])
        plt.plot(isochrone[:, 0], isochrone[:, 1], transform=crs.PlateCarree(), linewidth=0.1, color='black')
    # plt.plot([start.x, end.x], [start.y, end.y], transform=crs.Geodetic())
    plt.scatter(x=[start.x, end.x], y=[start.y, end.y], transform=crs.PlateCarree())
    plt.show()
