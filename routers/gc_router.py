from routers.router import Router
from routing_point import RoutingPoint
from util import angle360


class GCRouter(Router):
    def __init__(self, *args):
        super().__init__(*args)
        self.route_points = None

    def calculate_routing(self, n=20):
        az, _, dist = self.g.inv(self.start_point.x, self.start_point.y, self.end_point.x, self.end_point.y)
        d = 0
        route_points = [RoutingPoint(self.start_point.x, self.start_point.y, az, None, d, None, 0, 0)]
        for _ in range(n):
            d += dist / n
            current_x, current_y, az = self.g.fwd(route_points[-1].x, route_points[-1].y, az, dist / n)
            az = angle360(az + 180)
            v = self.polar.get_speed(current_x, current_y, az, 0, route_points[-1].time, self.wind)[0]
            route_points.append(RoutingPoint(current_x, current_y, az, route_points[-1], d, None, v,
                                             route_points[-1].time + dist / v / n))
        return route_points[-1]

    def get_isochrones(self):
        return [[x] for x in self.route_points]
