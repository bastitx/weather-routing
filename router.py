from pyproj import Geod
import numpy as np

from polar import Polar
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
        az, _, dist = self.g.inv(self.start_point.x, self.start_point.y, self.end_point.x, self.end_point.y)
        isochrones = [[RoutingPoint(self.start_point.x, self.start_point.y, az, None, 0, az, 0)]]
        min_dist = (dist, isochrones[0][0])
        current_min = min_dist
        while current_min[0] <= min_dist[0]:
            min_dist = current_min
            isochrones.append(self.next_isochrone(isochrones[-1], az))
            current_min = min([(self.g.inv(x.x, x.y, self.end_point.x, self.end_point.y)[2], x) for x in isochrones[-1]])
        return isochrones, min_dist[1]

    def great_circle_route(self, n=20):
        az, _, dist = self.g.inv(self.start_point.x, self.start_point.y, self.end_point.x, self.end_point.y)
        print(f'GC Distance: {round(dist/1000, 1)}km')
        route_points = [RoutingPoint(self.start_point.x, self.start_point.y, az, None, None, None, 0)]
        for _ in range(n):
            current_x, current_y, az = self.g.fwd(route_points[-1].x, route_points[-1].y, az, dist / n)
            az = angle360(az + 180)
            s = self.polar.get_speed(current_x, current_y, az, 0, 0, self.wind)
            route_points.append(RoutingPoint(current_x, current_y, az, route_points[-1], None, None, s))
        return route_points

    def next_isochrone(self, previous_isochrone, start_bearing, bearing_range=20, angle_range=20):
        isochrone = []
        for start_point in previous_isochrone:
            az = start_point.course
            for angle in range(-angle_range, angle_range):
                angle = angle360(az + angle)
                s = self.polar.get_speed(start_point.x, start_point.y, angle, 0, 0, self.wind)
                x, y, new_az = self.g.fwd(start_point.x, start_point.y, angle, s * 3600 * 24)
                new_az = angle360(new_az+180)
                az12, _, dist = self.g.inv(self.start_point.x, self.start_point.y, x, y)
                isochrone.append(RoutingPoint(x, y, new_az, start_point, dist, az12, s))
        best_per_sector = {}
        decimals = 0
        rounded_start_bearing = round(start_bearing, decimals)
        for x in isochrone:
            key = round(x.bearing, decimals)
            if abs(key - rounded_start_bearing) < bearing_range:
                if key in best_per_sector:
                    if x.distance_to_start > best_per_sector[key].distance_to_start:
                        best_per_sector[key] = x
                else:
                    best_per_sector[key] = x
        return [x for x in best_per_sector.values()]


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

    r = Router(start, end, p, w)
    isochrones, best_point = r.calculate_routing()
    gc_route = r.great_circle_route(20)
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
    p = gc_route[-1]
    while p.previous_point is not None:
        plt.plot([p.x, p.previous_point.x], [p.y, p.previous_point.y], transform=crs.PlateCarree(), c=color(p.speed))
        p = p.previous_point
    p = best_point
    while p.previous_point is not None:
        plt.plot([p.x, p.previous_point.x], [p.y, p.previous_point.y], transform=crs.PlateCarree(), c=color(p.speed))
        p = p.previous_point
    for isochrone in isochrones:
        isochrone = np.array([[x.x, x.y] for x in isochrone])
        plt.plot(isochrone[:, 0], isochrone[:, 1], transform=crs.PlateCarree(), linewidth=0.1, color='black')
    # plt.plot([start.x, end.x], [start.y, end.y], transform=crs.Geodetic())
    plt.scatter(x=[start.x, end.x], y=[start.y, end.y], transform=crs.PlateCarree())
    plt.show()
