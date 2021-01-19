import os
import tempfile
import time
from subprocess import call

import requests
import numpy as np
import scipy.io as sio


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

    def get_weather_data(self, metric='u_10m', run='00', hours='000'):
        date = time.strftime("%Y%m%d", time.gmtime())
        filename = f'icon_global_{date}{run}_{hours}_{metric.upper()}'
        nc_file = os.path.join(self.path, f'{filename}.nc')
        if not os.path.isfile(nc_file):
            url = f'https://opendata.dwd.de/weather/nwp/icon/grib/{run}/{metric.lower()}/' \
                  f'icon_global_icosahedral_single-level_{date}{run}_{hours}_{metric.upper()}.grib2.bz2'
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

    def extract_data(self, filename, key):
        nc_file = os.path.join(self.path, f'{filename}.nc')
        with sio.netcdf_file(nc_file) as f:
            data = f.variables[key]
            if len(data.shape) == 3:
                data = np.array(data[0, :, :])
            elif len(data.shape) == 4:
                data = np.array(data[0, 0, :, :])
            lons = np.array(f.variables['lon'][:])
            lats = np.array(f.variables['lat'][:])
        return data, lats, lons


if __name__ == '__main__':
    l = GRIBLoader(path='./tmp')
    l.get_weather_data()
