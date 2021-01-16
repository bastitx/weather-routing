from routers.router import Router
from routing_point import RoutingPoint
from util import angle360


class GCRouter(Router):
    def __init__(self, *args):
        super().__init__(*args)
        self.route_points = None

    def calculate_routing(self, n=20):
        az, _, dist = self.g.inv(self.start_point.x, self.start_point.y, self.end_point.x, self.end_point.y)
        print(f'GC Distance: {round(dist / 1000, 1)}km')
        route_points = [RoutingPoint(self.start_point.x, self.start_point.y, az, None, None, None, 0)]
        for _ in range(n):
            current_x, current_y, az = self.g.fwd(route_points[-1].x, route_points[-1].y, az, dist / n)
            az = angle360(az + 180)
            s = self.polar.get_speed(current_x, current_y, az, 0, 0, self.wind)
            route_points.append(RoutingPoint(current_x, current_y, az, route_points[-1], None, None, s))
        return route_points[-1]

    def get_isochrones(self):
        return [[x] for x in self.route_points]
