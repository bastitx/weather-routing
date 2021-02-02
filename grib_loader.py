import datetime
import os
import tempfile
import time
from subprocess import call

import pytz
import requests
import numpy as np
import scipy.io as sio
import scipy.interpolate as sip


class GRIBLoader:
    def __init__(self, path=None):
        self.path = path if path else tempfile.gettempdir()

        grid_dir = os.path.join(self.path, 'ICON_GLOBAL2WORLD_025_EASY/')
        if not os.path.exists(grid_dir):
            r = requests.get('https://opendata.dwd.de/weather/lib/cdo/ICON_GLOBAL2WORLD_025_EASY.tar.bz2', stream=True)
            r.raise_for_status()
            grid_tar = os.path.join(self.path, 'ICON_GLOBAL2WORLD_025_EASY.tar.bz2')
            with open(grid_tar, 'wb') as fd:
                for block in r.iter_content(chunk_size=1024):
                    fd.write(block)
            rt = call(['tar', 'xf', grid_tar, '-C', self.path])
            if rt != 0:
                raise SystemError('Could not untar file')
            rt = call(['rm', grid_tar])
            if rt != 0:
                raise SystemError("Error with remove")

        self.target_file = os.path.join(grid_dir, 'target_grid_world_025.txt')
        self.weight_file = os.path.join(grid_dir, 'weights_icogl2world_025.nc')

        now = datetime.datetime.utcnow()
        if now.hour < 4:
            now -= datetime.timedelta(hours=12)
            self.run = '12'
        else:
            self.run = '00'
        self.today = datetime.datetime(year=now.year, month=now.month, day=now.day, hour=0 if self.run == '00' else 12,
                                       tzinfo=pytz.utc)

        self.wind_direction = {}
        self.wind_velocity = {}

    def get_weather_data(self, metric='u_10m', hours='000'):
        date = time.strftime("%Y%m%d", self.today.timetuple())
        filename = f'icon_global_{date}{self.run}_{hours}_{metric.upper()}'
        nc_file = os.path.join(self.path, f'{filename}.nc')
        if not os.path.isfile(nc_file):
            url = f'https://opendata.dwd.de/weather/nwp/icon/grib/{self.run}/{metric.lower()}/' \
                  f'icon_global_icosahedral_single-level_{date}{self.run}_{hours}_{metric.upper()}.grib2.bz2'
            r = requests.get(url, stream=True)
            r.raise_for_status()
            bz2_file = os.path.join(self.path, f'{filename}.grib2.bz2')
            with open(bz2_file, 'wb') as fd:
                for block in r.iter_content(chunk_size=1024):
                    fd.write(block)

            rt = call(['bzip2', '-d', bz2_file])
            if rt != 0:
                raise RuntimeError('Bzip2 failed.')
            grib2_file = os.path.join(self.path, f'{filename}.grib2')
            rt = call(['cdo', '-f', 'nc', f'remap,{self.target_file},{self.weight_file}', grib2_file, nc_file])
            if rt != 0:
                raise RuntimeError('CDO failed.')
            rt = call(['rm', grib2_file])
            if rt != 0:
                raise RuntimeError('Removing GRIB2 failed.')
        return nc_file

    @staticmethod
    def extract_data(filename, key):
        with sio.netcdf_file(filename) as f:
            data = f.variables[key]
            if len(data.shape) == 3:
                data = np.array(data[0, :, :])
            elif len(data.shape) == 4:
                data = np.array(data[0, 0, :, :])
            lons = np.array(f.variables['lon'][:])
            lats = np.array(f.variables['lat'][:])
            f.close()
            return data, lats, lons

    def get_wind_velocity_direction(self, time, force_file_read=False):
        forecast = round((time - self.today.timestamp()) / 60 / 60)
        if forecast > 78:
            m = forecast % 3
            if m == 1:
                forecast -= 1
            elif m == 2:
                forecast += 1
        forecast_in_dicts = forecast in self.wind_velocity and forecast in self.wind_direction
        if force_file_read or not forecast_in_dicts:
            filename = self.get_weather_data(metric='u_10m', hours=f"{forecast:03}")
            u, lats, lons = self.extract_data(filename, '10u')
            filename = self.get_weather_data(metric='v_10m', hours=f"{forecast:03}")
            v, lats, lons = self.extract_data(filename, '10v')
            velocity = np.sqrt(u**2 + v**2)
            direction = np.arccos(v / velocity)
            if not forecast_in_dicts:
                self.wind_velocity[forecast] = sip.interp2d(lons, lats, velocity)
                self.wind_direction[forecast] = sip.interp2d(lons, lats, direction)
            return forecast, velocity, direction, lats, lons
        else:
            return forecast, self.wind_velocity[forecast], self.wind_direction[forecast], None, None

    def get_wind(self, timestamp, loc):
        forecast, *_ = self.get_wind_velocity_direction(timestamp)
        direction = self.wind_direction[forecast](loc.x, loc.y)
        velocity = self.wind_velocity[forecast](loc.x, loc.y)
        return direction, velocity

    def display_wind(self, timestamp):
        _, velocity, _, lats, lons = self.get_wind_velocity_direction(timestamp, force_file_read=True)
        return lats, lons, velocity


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    import cartopy.crs as crs
    l = GRIBLoader(path='./tmp')
    t = datetime.datetime.utcnow().timestamp()
    lats, lons, data = l.display_wind(t)
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1, projection=crs.Mercator())
    # ax.set_global()
    ax.coastlines()
    plt.pcolormesh(lons, lats, data, transform=crs.PlateCarree())
    plt.show()
