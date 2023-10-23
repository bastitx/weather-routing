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

from util import angle360


class GRIBLoader:
    '''Loads GRIB files from DWD and interpolates them to a regular grid'''
    
    def __init__(self, path=None):
        self.path = path if path else tempfile.gettempdir()

        grid_dir = os.path.join(self.path, 'ICON_GLOBAL2WORLD_025_EASY/')
        if not os.path.exists(grid_dir):
            grid_tar = os.path.join(self.path, 'ICON_GLOBAL2WORLD_025_EASY.tar.bz2')
            self.download_file('https://opendata.dwd.de/weather/lib/cdo/ICON_GLOBAL2WORLD_025_EASY.tar.bz2', grid_tar)

            rt = call(['tar', 'xf', grid_tar, '-C', self.path])
            if rt != 0:
                raise SystemError('Could not untar file')
            rt = call(['rm', grid_tar])
            if rt != 0:
                raise SystemError("Error with remove")

        self.target_file = os.path.join(grid_dir, 'target_grid_world_025.txt')
        self.weight_file = os.path.join(grid_dir, 'weights_icogl2world_025.nc')

        self.clima_file = os.path.join(self.path, 'uvclm95to05.nc')
        if not os.path.exists(self.clima_file):
            self.download_file('https://www.ncei.noaa.gov/thredds/fileServer/uv/clm/uvclm95to05.nc', self.clima_file)

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

    def get_dwd_weather_data(self, metric='u_10m', hours='000'):
        date = time.strftime("%Y%m%d", self.today.timetuple())
        filename = f'icon_global_{date}{self.run}_{hours}_{metric.upper()}'
        nc_file = os.path.join(self.path, f'{filename}.nc')
        if not os.path.isfile(nc_file):
            url = f'https://opendata.dwd.de/weather/nwp/icon/grib/{self.run}/{metric.lower()}/' \
                  f'icon_global_icosahedral_single-level_{date}{self.run}_{hours}_{metric.upper()}.grib2.bz2'
            bz2_file = os.path.join(self.path, f'{filename}.grib2.bz2')
            self.download_file(url, bz2_file)

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
    def download_file(url, filename):
        r = requests.get(url, stream=True)
        r.raise_for_status()
        with open(filename, 'wb') as fd:
            for block in r.iter_content(chunk_size=1024):
                fd.write(block)

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
        return data, lats, lons

    @staticmethod
    def extract_data_time(filename, key):
        with sio.netcdf_file(filename) as f:
            data = f.variables[key]
            if len(data.shape) == 3:
                data = np.array(data[:, :, :])
            elif len(data.shape) == 4:
                data = np.array(data[:, 0, :, :])
            lons = np.array(f.variables['lon'][:])
            lats = np.array(f.variables['lat'][:])
        return data, lats, lons

    def get_uv_dwd(self, forecast):
        filename = self.get_dwd_weather_data(metric='u_10m', hours=f"{forecast:03}")
        u, lats, lons = self.extract_data(filename, '10u')
        filename = self.get_dwd_weather_data(metric='v_10m', hours=f"{forecast:03}")
        v, lats, lons = self.extract_data(filename, '10v')
        return u, v, lats, lons

    def get_uv_clima(self):
        u, lats, lons = self.extract_data_time(self.clima_file, 'u')
        v, lats, lons = self.extract_data_time(self.clima_file, 'v')
        u = np.where(np.abs(u) > 1000, 1e-10, u)
        v = np.where(np.abs(v) > 1000, 1e-10, v)
        return u, v, lats, lons

    def get_wind_velocity_direction(self, time, force_file_read=False):
        forecast = round((time - self.today.timestamp()) / 60 / 60)
        # After 78h, the forecast is only available in 3h steps, so we round to the nearest 3h step
        if 78 < forecast <= 180:
            m = forecast % 3
            if m == 1:
                forecast -= 1
            elif m == 2:
                forecast += 1
            forecast_str = str(forecast)
        # After 180h, we fallback to monthly climatology
        elif forecast > 180:
            month = datetime.datetime.utcfromtimestamp(time).month - 1
            forecast_str = f'm{month}'
        # Below 78h, the forecast is available in 1h steps
        else:
            forecast_str = str(forecast)
        forecast_in_dicts = forecast_str in self.wind_velocity and forecast_str in self.wind_direction
        # Load file if it is not in memory yet or if we want to force a file read
        if force_file_read or not forecast_in_dicts:
            if forecast <= 180:
                u, v, lats, lons = self.get_uv_dwd(forecast)
                velocity = np.sqrt(u**2 + v**2)
                direction = angle360(np.rad2deg(np.arccos(v / velocity)))
            elif self.clima_file:
                u, v, lats, lons = self.get_uv_clima()
                velocity = np.sqrt(u**2 + v**2)
                # When velocity is NaN or a very small number, we set it to 1e-10 to avoid division by zero
                velocity = np.where(velocity == np.nan, 1e-10, np.where(velocity < 1e-10, 1e-10, velocity))
                acos = v / velocity
                # Clip acos to [-1, 1] to avoid NaNs
                acos = np.where(acos > 1, 1, np.where(acos < -1, -1, acos))
                direction = angle360(np.rad2deg(np.arccos(acos)))
            else:
                raise FileNotFoundError()
            # Store interpolators in memory
            if not forecast_in_dicts:
                if len(u.shape) == 2:
                    self.wind_velocity[forecast_str] = sip.interp2d(lons, lats, velocity)
                    self.wind_direction[forecast_str] = sip.interp2d(lons, lats, direction)
                else:
                    for m in range(u.shape[0]):
                        self.wind_velocity[f'm{m}'] = sip.interp2d(lons, lats, velocity[m])
                        self.wind_direction[f'm{m}'] = sip.interp2d(lons, lats, direction[m])
            if len(u.shape) == 2:
                return forecast_str, velocity, direction, lats, lons
            else:
                return forecast_str, velocity[month], direction[month], lats, lons
        else:
            return forecast_str, self.wind_velocity[forecast_str], self.wind_direction[forecast_str], None, None

    def get_wind(self, timestamp, loc):
        forecast, *_ = self.get_wind_velocity_direction(timestamp)
        direction = self.wind_direction[forecast](loc.x, loc.y)
        velocity = self.wind_velocity[forecast](loc.x, loc.y)
        return direction, velocity

    def display_wind(self, timestamp):
        # _, velocity, _, lats, lons = self.get_wind_velocity_direction(timestamp, force_file_read=True)
        u, v, lats, lons = self.get_uv_clima()
        month = datetime.datetime.utcfromtimestamp(timestamp).month - 1
        return u[month], v[month], lats, lons


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    import cartopy.crs as crs
    l = GRIBLoader(path='./tmp')
    t = (datetime.datetime.utcnow() + datetime.timedelta(days=1)).timestamp()
    u, v, lats, lons = l.display_wind(t)
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1, projection=crs.Mercator())
    # ax.set_global()
    ax.coastlines()
    plt.barbs(lons[::20], lats[::20], u[::20, ::20], v[::20, ::20], length=3, transform=crs.PlateCarree())
    plt.show()
