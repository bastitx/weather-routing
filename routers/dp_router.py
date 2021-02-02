from routers.gc_router import GCRouter
from routers.router import Router
from routing_point import RoutingPoint
from util import angle360

import numpy as np


class DPRouter(Router):
    def __init__(self, nodes, layers, *args):
        super().__init__(*args)
        self._create_mesh(nodes, layers, args=args)

    def _create_mesh(self, nodes=40, layers=30, args=None):
        self.gc = GCRouter(*args)
        p = self.gc.calculate_routing(layers)
        dist = p.distance_to_start
        p = p.previous_point  # skip end point
        self.mesh = [[RoutingPoint(self.end_point.x, self.end_point.y, None, None, None, None, None, None)]]
        while p.previous_point is not None:
            angle = angle360(p.course + 90)
            layer = []
            for d in np.linspace(-dist / 5, dist / 5, nodes):
                x, y, az = self.g.fwd(p.x, p.y, angle, d)
                layer.append(RoutingPoint(x, y, None, None, None, None, None, None))
            self.mesh.append(layer)
            p = p.previous_point
        self.mesh.append([RoutingPoint(self.start_point.x, self.start_point.y, None, None, 0, None, 0, self.start_time)])
        self.mesh = [x for x in reversed(self.mesh)]

    def calculate_routing(self):
        for i in range(len(self.mesh) - 1):
            for start in self.mesh[i]:
                if start.time == np.inf:
                    continue
                for end in self.mesh[i+1]:
                    az, _, dist = self.g.inv(start.x, start.y, end.x, end.y)
                    v = self.polar.get_speed(start, az, 0, start.time, self.wind)[0]
                    t_end = start.time + dist / v
                    if end.time is None or t_end < end.time:
                        end.time = t_end
                        end.previous_point = start
                        end.course = az
                        end.speed = v
                        end.distance_to_start = start.distance_to_start + dist
        return self.mesh[-1][0]

    def get_isochrones(self):
        return self.mesh
