from routers.router import Router
from routing_point import RoutingPoint
from util import angle360
import numpy as np


class IsochroneRouter(Router):
    '''
    Isochrone Router. An isochrone is a line of equal travel time. We create a mesh of isochrones and find the
    shortest path from start to end point. 
    '''

    def __init__(self, time_step, *args):
        super().__init__(*args)
        self.isochrones = None
        self.time_step = time_step

    def calculate_routing(self):
        '''
        Calculate the shortest path from start to end point. This is inspired by 
        https://github.com/mak08/Bitsailor/blob/027c3fb699f7ef090349d3eb8fd4fc0b16f06987/simulation.cl#L39.
        '''
        # Calculate initial course (forward azimuth) and distance from start to end point
        az, _, dist = self.g.inv(self.start_point.x, self.start_point.y, self.end_point.x, self.end_point.y)
        # Calculate initial isochrone
        self.isochrones = [[RoutingPoint(self.start_point.x, self.start_point.y, az, None, 0, az, 0, self.start_time)]]
        min_dist = (dist, self.isochrones[0][0])
        current_min = min_dist
        while current_min[0] <= min_dist[0]:
            min_dist = current_min
            self.isochrones.append(self._next_isochrone(self.isochrones[-1], az))
            current_min = min([(self.g.inv(x.x, x.y, self.end_point.x, self.end_point.y)[2], x) for x in self.isochrones[-1]])
        return min_dist[1]

    def get_isochrones(self):
        return self.isochrones

    def _next_isochrone(self, previous_isochrone: list[RoutingPoint], start_bearing: float, bearing_range=20, angle_range=20):
        '''Calculate the next isochrone starting from the previous one.'''
        isochrone = []
        # Iterate over all points in previous isochrone
        for start_point in previous_isochrone:
            az = start_point.course
            # Iterate over all full degree angles in range
            for angle in range(-angle_range, angle_range):
                angle = angle360(az + angle)
                # Get speed from current wind at current location and time
                v = self.polar.get_speed(start_point, angle, 0, start_point.time, self.wind)
                # Calculate new location and azimuth by travelling for one time step in the given direction at the given speed
                x, y, new_az = self.g.fwd(start_point.x, start_point.y, angle, v * self.time_step)
                new_az = angle360(new_az+180)
                # Calculate bearing and distance from start point
                az12, _, dist = self.g.inv(self.start_point.x, self.start_point.y, x, y)
                isochrone.append(RoutingPoint(x, y, new_az, start_point, dist, az12, v, start_point.time + self.time_step))

        # Iterate over all points in isochrone and find the best point in each sector
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
