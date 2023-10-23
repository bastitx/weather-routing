from routers.gc_router import GCRouter
from routers.router import Router
from routing_point import RoutingPoint
from util import angle360

import numpy as np


class DPRouter(Router):
    '''Dynamic Programming Router'''

    def __init__(self, nodes, layers, *args):
        super().__init__(*args)
        self._create_mesh(nodes, layers, args=args)

    def _create_mesh(self, nodes=40, layers=30, args=None):
        '''
        Create a mesh of nodes. Each node has a course, speed and time to reach the end point. The mesh is created
        by calculating the shortest path from end to start point and adding nodes on each side of the path.
        '''
        # Create mesh by calculating great circle route from end to start point
        self.gc = GCRouter(*args)
        p = self.gc.calculate_routing(layers, constant_speed=5)
        dist = p.distance_to_start
        p = p.previous_point  # skip end point
        self.mesh = [[RoutingPoint(self.end_point.x, self.end_point.y, None, None, None, None, None, None)]]
        # Iterate over linked list from end to start
        while p.previous_point is not None:
            angle = angle360(p.course + 90)
            layer = []
            # Add nodes on each side of the path. The width of the path is proportional to the distance to the end point.
            for d in np.linspace(-dist / 5, dist / 5, nodes):
                x, y, az = self.g.fwd(p.x, p.y, angle, d)
                layer.append(RoutingPoint(x, y, None, None, None, None, None, None))
            self.mesh.append(layer)
            p = p.previous_point
        self.mesh.append([RoutingPoint(self.start_point.x, self.start_point.y, None, None, 0, None, 0, self.start_time)])
        self.mesh = [x for x in reversed(self.mesh)]

    def calculate_routing(self):
        # Iterate over all nodes in the mesh and calculate the time to reach the end point
        for i in range(len(self.mesh) - 1):
            for start in self.mesh[i]:
                # Skip nodes that are already over the max time
                if start.time > self.max_time:
                    continue
                # Iterate over all nodes in the next layer
                for end in self.mesh[i+1]:
                    # Calculate course and distance from start to end point
                    az, _, dist = self.g.inv(start.x, start.y, end.x, end.y)
                    v = self.polar.get_speed(start, az, 0, start.time, self.wind)[0]
                    t_end = start.time + dist / v
                    # Update node if time to reach end point is shorter than previous time
                    if end.time is None or t_end < end.time:
                        end.time = t_end
                        end.previous_point = start
                        end.course = az
                        end.speed = v
                        end.distance_to_start = start.distance_to_start + dist
        return self.mesh[-1][0]

    def get_isochrones(self):
        return self.mesh
