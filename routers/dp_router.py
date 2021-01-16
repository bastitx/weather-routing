from shapely.geometry import Point

from routers.gc_router import GCRouter
from routers.router import Router
from util import angle360

import numpy as np


class DPRouter(Router):
    def __init__(self, *args):
        super().__init__(*args)
        self._create_mesh(*args)

    def _create_mesh(self, *args):
        self.gc = GCRouter(*args)
        p = self.gc.calculate_routing()
        dist = p.distance_to_start
        p = p.previous_point  # skip end point
        self.mesh = []
        while p.previous_point is not None:
            angle = angle360(p.course + 90)
            layer = []
            for d in np.linspace(-dist / 4, dist / 4, 20):
                x, y, az = self.g.fwd(p.x, p.y, angle, d)
                layer.append(Point(x, y))
            self.mesh.append(layer)
            p = p.previous_point

    def calculate_routing(self):
        pass

    def get_isochrones(self):
        return self.mesh
