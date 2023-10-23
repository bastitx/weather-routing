from shapely.geometry import Point


class RoutingPoint:

    def __init__(self, x, y, course, previous_point, distance_to_start, bearing, speed, time):
        self.point = Point(x, y)
        self.course = course  # degrees
        self.previous_point = previous_point  # RoutingPoint
        self.distance_to_start = distance_to_start  # m
        self.bearing = bearing  # degrees
        self.speed = speed  # m/s
        self.time = time  # s since epoch UTC

    @property
    def x(self):
        return self.point.x
    
    @property
    def y(self):
        return self.point.y
