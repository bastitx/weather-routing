from pyproj import Geod
import numpy as np

from polar import Polar
from util import CRS, angle360
from wind import Wind


class Router:
    def __init__(self, start_point, end_point, polar, wind):
        self.start_point = start_point
        self.end_point = end_point
        self.polar = polar
        self.wind = wind

    def calculate_routing(self, n, angle_range=20):
        g = Geod(ellps='WGS84')
        az12, az21, dist = g.inv(self.start_point.x, self.start_point.y, self.end_point.x, self.end_point.y)
        print(f'Distance: {dist}m')
        route_points = []
        speeds = [[0]]
        current_x, current_y = self.start_point.xy
        route_points.append(np.array([current_x, current_y]).flatten())
        isochrones = []
        az = az12
        for i in range(n):
            isochrone = []
            for angle in range(-angle_range, angle_range):
                angle = angle360(az + angle)
                s = self.polar.get_speed(current_x, current_y, angle, 0, 0, self.wind)
                x, y, _ = g.fwd(current_x, current_y, angle, s*3600*24)
                isochrone.append(np.array([x, y]).flatten())
            current_x, current_y, az = g.fwd(current_x, current_y, az, dist/n)
            az = angle360(az + 180)
            isochrones.append(isochrone)
            speeds.append(self.polar.get_speed(current_x, current_y, az, 0, 0, self.wind))
            route_points.append(np.array([current_x, current_y]).flatten())
        return np.array(route_points), np.array(speeds).flatten(), np.array(isochrones)


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    import cartopy.crs as crs
    from shapely.geometry import Point, LineString

    start = Point(-4.91519, 48.26118)
    end = Point(-74.71870, 38.86484)

    p = np.array([[0., 45., 90., 135., 180.], [0., 0., 2.8, 4.2, 2.8]])
    p = Polar(p)
    w = Wind(150., 20.)

    r = Router(start, end, p, w)
    route, speeds, isochrones = r.calculate_routing(20)
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
    for i, r in enumerate(route):
        if i > 0:
            plt.plot([p_r[0], r[0]], [p_r[1], r[1]], transform=crs.PlateCarree(), c=color(speeds[i]))
        p_r = r
    for j, isochrone in enumerate(isochrones):
        for i, p in enumerate(isochrone):
            if i > 0:
                plt.plot([p_p[0], p[0]], [p_p[1], p[1]], transform=crs.PlateCarree(), c='black')
                plt.plot([route[j][0], p[0]], [route[j][1], p[1]], transform=crs.PlateCarree(), c='black', linewidth=0.1)
            p_p = p
    # plt.plot([start.x, end.x], [start.y, end.y], transform=crs.Geodetic())
    plt.scatter(x=[start.x, end.x], y=[start.y, end.y], transform=crs.PlateCarree())
    plt.show()
