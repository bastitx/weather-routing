from shapely.geometry import Point


class RoutingPoint(Point):
    def __init__(self, x, y, course, previous_point, distance_to_start, bearing, speed):
        super().__init__(x, y)
        self.course = course
        self.previous_point = previous_point
        self.distance_to_start = distance_to_start
        self.bearing = bearing
        self.speed = speed
