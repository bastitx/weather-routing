import numpy as np

CRS = 'EPSG:4326'


def angle360(angle):
    '''Converts an angle to the range [0, 360)'''
    return np.where(angle < 0, angle+360, np.where(angle >= 360, angle-360, angle))

