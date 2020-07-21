import os
from netCDF4 import Dataset
import cftime as cft
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import datetime

class CDFDay():
    
    def __init__(self, root_path, date):
        self.date = date
        self.root_path = root_path

        hgt_path = os.path.join(root_path,'hgts',f'hgt.{date.year}.nc')
        self.hgts = self.retrieve_data('hgt',hgt_path, date, save_coords=True)
        
        uwnd_path = os.path.join(root_path,'u_winds',f'uwnd.{date.year}.nc')
        self.uwnds = self.retrieve_data('uwnd',uwnd_path, date)
        
        vwnd_path = os.path.join(root_path,'v_winds',f'vwnd.{date.year}.nc')
        self.vwnds = self.retrieve_data('vwnd',vwnd_path, date)

        self.winds = np.sqrt(np.square(self.uwnds) + np.square(self.vwnds))

        self.localize()


    def retrieve_data(self, name, path, date, save_coords=False):
        # date should be datetime.datetime object

        fh = Dataset(path, mode='r')
        
        # Get index of day for requested day
        times = fh.variables['time'][:].data
        times = cft.num2pydate(times, fh.variables['time'].units, calendar='standard')
        
        data_index = np.argwhere(times == date)[0,0]
        
        if save_coords:
            self.lons = fh.variables['lon'][:].data
            self.lats = fh.variables['lat'][:].data
        
        return fh.variables[name][data_index].data


    def localize(self, lat0=20, lat1=70, lon0=220, lon1=340): # Default US localization

        lat_mask = ((self.lats >= lat0) & (self.lats <= lat1))
        self.loc_lats = self.lats[lat_mask]

        lon_mask = ((self.lons >= lon0) & (self.lons <= lon1))
        self.loc_lons = self.lons[lon_mask]

        start_lat = np.argwhere(lat_mask).min()
        end_lat = np.argwhere(lat_mask).max()

        start_lon = np.argwhere(lon_mask).min()
        end_lon = np.argwhere(lon_mask).max()

        self.loc_hgts = self.hgts[..., start_lat:end_lat+1, start_lon:end_lon+1]

        self.loc_uwnds = self.uwnds[..., start_lat:end_lat+1, start_lon:end_lon+1]
        self.loc_vwnds = self.vwnds[..., start_lat:end_lat+1, start_lon:end_lon+1]
        self.loc_winds = np.sqrt(np.square(self.loc_uwnds) + np.square(self.loc_vwnds))


class Matches():
    
    def __init__(self, root_path, match_df):
        
        self.days = []

        for i in range(match_df.shape[0]):
            date = match_df.iloc[i].date.to_pydatetime()
            score = match_df.iloc[i].score

            cdf_day = CDFDay(root_path, date)
            cdf_day.score = score
            self.days.append(cdf_day)


    def plot(self, data, n, level, loc=True, contours=5, figsize=(15, 4), cmap='YlOrRd'):
        
        cdf = self.days[n]
        date = cdf.date.strftime(r'%b %d %Y')
        title_str = f'{date} : Level {level} : Score {round(cdf.score,4)}'
        
        if data in ['hgts', 'uwnd', 'vwnd', 'wnd']:
            fig = plt.figure(figsize=figsize)
            ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
            fig.suptitle(title_str, fontsize=16)

        if loc:
            hgts = cdf.loc_hgts[level-1]
            u_winds = cdf.loc_uwnds[level-1]
            v_winds = cdf.loc_vwnds[level-1]
            winds = cdf.loc_winds[level-1]
            lats = cdf.loc_lats
            lons = cdf.loc_lons
        else:
            hgts = cdf.hgts[level-1]
            u_winds = cdf.u_winds[level-1]
            v_winds = cdf.v_winds[level-1]
            winds = cdf.winds[level-1]
            lats = cdf.lats
            lons = cdf.lons


        def plot_data(values, title, ax):
            cf = ax.contourf(lons, lats, values, 200, transform=ccrs.PlateCarree(), cmap=cmap)
            ax.coastlines()
            ax.set_title(title)

            fig.colorbar(cf, ax=ax, orientation='horizontal', pad=0.03)
            
            if contours and not 'wind' in title.lower():
                cs = ax.contour(lons, lats, values, contours, transform=ccrs.PlateCarree())
                ax.clabel(cs, inline=1, fmt='%1.0f')
        
        def gradient(arr):
    
            x_grad_kernel = np.array([[-1,0,1]])
            y_grad_kernel = x_grad_kernel.reshape(-1,1)

            x_grad = convolve(arr,x_grad_kernel)
            y_grad = convolve(arr,y_grad_kernel)

            grad = np.sqrt(np.square(x_grad) + np.square(y_grad))

            return grad

        if data == 'hgts':
            plot_data(hgts, 'Geopotential Heights', ax)

        elif data == 'uwnd':
            plot_data(u_winds, 'U Winds', ax)

        elif data == 'vwnd':
            plot_data(v_winds, 'V Winds', ax)

        elif data == 'wnd':
            plot_data(winds, 'Total Wind', ax)
        
        elif data == 'grad':
            grad = gradient(cdf.loc_hgts[level-1])
            plot_data(grad,'Pressure Gradient',ax)

        else:
            fig, axes = plt.subplots(1, 2, figsize=figsize, subplot_kw={'projection': ccrs.PlateCarree()})

            plot_data(hgts, 'Geopotential Heights',axes[0])
            axes[0].coastlines()

            plot_data(winds, 'Total Wind Speed', axes[1])
            axes[1].coastlines()
            
            fig.suptitle(title_str, fontsize=16)

            return fig, axes
        
        return fig, ax


    def quiver(self, n, level, loc=True):
        
        cdf = self.days[n]

        fig, ax = plt.subplots(1,1, figsize=(12,5), subplot_kw={'projection': ccrs.PlateCarree()})
        ax.coastlines()
        if loc:
            X = cdf.loc_lons
            Y = cdf.loc_lats
            U = cdf.loc_uwnds[level-1]
            V = cdf.loc_vwnds[level-1]
            C = cdf.loc_winds[level-1]
        else:
            X = cdf.lons
            Y = cdf.lats
            U = cdf.uwnds[level-1]
            V = cdf.vwnds[level-1]
            C = cdf.winds[level-1]

        ax.quiver(X,Y,U,V,C, cmap='YlOrRd', transform = ccrs.PlateCarree())
        ax.set_xlabel('Longitudes')
        ax.set_ylabel('Latitudes')
        
        return fig, ax