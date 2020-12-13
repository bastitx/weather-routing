import matplotlib.pyplot as plt
import cartopy.crs as crs
import cartopy.feature as cfeature


class Visualizer:

    def visualize(self, route=None):
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1, projection=crs.PlateCarree())
        ax.add_feature(cfeature.COASTLINE)
        if route:
            plt.plot()
        plt.show()
