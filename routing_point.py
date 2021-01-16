class RoutingPoint:
    def __init__(self, x, y, course, previous_point, distance_to_start, bearing, speed):
        self.x = x
        self.y = y
        self.course = course
        self.previous_point = previous_point
        self.distance_to_start = distance_to_start
        self.bearing = bearing
        self.speed = speed

    def __lt__(self, other):
        return self.distance_to_start < other.distance_to_start
