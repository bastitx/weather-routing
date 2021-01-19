from routers.router import Router
from routing_point import RoutingPoint
from util import angle360


class IsochroneRouter(Router):
    def __init__(self, *args):
        super().__init__(*args)
        self.isochrones = None

    def calculate_routing(self):
        az, _, dist = self.g.inv(self.start_point.x, self.start_point.y, self.end_point.x, self.end_point.y)
        self.isochrones = [[RoutingPoint(self.start_point.x, self.start_point.y, az, None, 0, az, 0, 0)]]
        min_dist = (dist, self.isochrones[0][0])
        current_min = min_dist
        while current_min[0] <= min_dist[0]:
            min_dist = current_min
            self.isochrones.append(self._next_isochrone(self.isochrones[-1], az))
            current_min = min([(self.g.inv(x.x, x.y, self.end_point.x, self.end_point.y)[2], x) for x in self.isochrones[-1]])
        return min_dist[1]

    def get_isochrones(self):
        return self.isochrones

    def _next_isochrone(self, previous_isochrone, start_bearing, bearing_range=20, angle_range=20, time_step=(3600*24)):
        isochrone = []
        for start_point in previous_isochrone:
            az = start_point.course
            for angle in range(-angle_range, angle_range):
                angle = angle360(az + angle)
                v = self.polar.get_speed(start_point, angle, 0, start_point.time, self.wind)
                x, y, new_az = self.g.fwd(start_point.x, start_point.y, angle, v * time_step)
                new_az = angle360(new_az+180)
                az12, _, dist = self.g.inv(self.start_point.x, self.start_point.y, x, y)
                isochrone.append(RoutingPoint(x, y, new_az, start_point, dist, az12, v, start_point.time + time_step))
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
