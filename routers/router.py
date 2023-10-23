import time

from pyproj import Geod
import numpy as np

from polar import Polar
from wind.constant_wind import ConstantWind
from wind.grib_wind import GRIBWind


class Router:
    '''Base class for routers'''

    def __init__(self, start_point, end_point, polar, wind, start_time, max_time, crs='WGS84'):
        self.start_point = start_point
        self.end_point = end_point
        self.polar = polar
        self.wind = wind
        self.start_time = start_time
        self.max_time = max_time
        self.g = Geod(ellps=crs)

    def calculate_routing(self):
        raise NotImplementedError()

    def get_isochrones(self):
        raise NotImplementedError()


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    import cartopy.crs as crs
    from shapely.geometry import Point, LineString
    from routers.gc_router import GCRouter
    from routers.dp_router import DPRouter
    from routers.isochrone_router import IsochroneRouter

    start = Point(-4.91519, 48.26118)
    end = Point(-74.71870, 38.86484)
    # end = Point(-60.69365, 14.77645)

    #start = Point(-18.5351, 63.3676)
    #end = Point(-5.1736668, 58.542698)

    p = np.array([[0., 45., 90., 135., 180.], [0., 0., 2.8, 4.2, 2.8]])
    p = Polar(p)
    w = GRIBWind()
    start_time = time.time() + 60 * 60 * 3
    max_time = time.time() + 60 * 60 * 24 * 365

    r = IsochroneRouter(3600 * 24 * 2, start, end, p, w, start_time, max_time)
    best_point_iso = r.calculate_routing()
    print(f'Isochrone Distance: {round(best_point_iso.distance_to_start / 1000, 1)}km')
    print(f'Isochrone Passage time: {round((best_point_iso.time - start_time) / 3600, 1)}h')
    # isochrones = r.get_isochrones()
    r = GCRouter(start, end, p, w, start_time, max_time)
    best_point_gc = r.calculate_routing(10)
    print(f'GC Distance: {round(best_point_gc.distance_to_start / 1000, 1)}km')
    print(f'GC Passage time: {round((best_point_gc.time - start_time) / 3600, 1)}h')
    r = DPRouter(20, 20, start, end, p, w, start_time, max_time)
    best_point_dp = r.calculate_routing()
    isochrones = r.get_isochrones()
    print(f'DP Distance: {round(best_point_dp.distance_to_start / 1000, 1)}km')
    print(f'DP Passage time: {round((best_point_dp.time - start_time) / 3600, 1)}h')
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

    points = []
    for p in [best_point_dp, best_point_gc, best_point_iso]:
        points += [[p.x, p.y]]
        while p.previous_point is not None:
            points += [[p.previous_point.x, p.previous_point.y]]
            plt.plot([p.x, p.previous_point.x], [p.y, p.previous_point.y], transform=crs.PlateCarree(), c=color(p.speed))
            p = p.previous_point
    bounds = LineString(points).bounds
    # ax.set_extent([bounds[0] - 1, bounds[2] + 1, bounds[1] - 1, bounds[3] + 1], crs=crs.PlateCarree())
    for isochrone in isochrones:
        isochrone = np.array([[x.x, x.y] for x in isochrone])
        # plt.scatter(isochrone[:, 0], isochrone[:, 1], transform=crs.PlateCarree(), s=0.1, color='black')
        plt.plot(isochrone[:, 0], isochrone[:, 1], transform=crs.PlateCarree(), linewidth=0.1, color='black')
    # plt.plot([start.x, end.x], [start.y, end.y], transform=crs.Geodetic())
    plt.scatter(x=[start.x, end.x], y=[start.y, end.y], transform=crs.PlateCarree())

    u, v, lats, lons = w.loader.display_wind(start_time)
    # plt.pcolormesh(lons, lats, data, transform=crs.PlateCarree())
    f = 10
    plt.barbs(lons[::f], lats[::f], u[::f, ::f], v[::f, ::f], length=4, linewidth=0.4, transform=crs.PlateCarree())
    plt.show()
