from netCDF4 import Dataset
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import datetime


class CDFData():
    
    def __init__(self, hgt_path, uwind_path=None, vwind_path=None):
        
        (self.year, self.times, self.lats, self.lons, self.hgts) = self.retrieve_data(hgt_path,'hgt')
        
        self.uwind_path = uwind_path
        self.vwind_path = vwind_path

        # Collect Wind data and assert shapes and year are compatible
        if uwind_path:
            (u_year,u_winds) = self.retrieve_data(uwind_path,'uwnd')
            assert u_year == self.year, "Wrong Year"
            assert u_winds.shape == self.hgts.shape, f"wind_shape!=hgts_shape\n{u_winds.shape} != {self.hgts.shape}"
            self.u_winds = u_winds

        if vwind_path:
            (v_year,v_winds) = self.retrieve_data(vwind_path,'vwnd')
            assert v_year == self.year, "Wrong Year"
            assert v_winds.shape == self.hgts.shape, f"wind_shape!=hgts_shape\n{v_winds.shape} != {self.hgts.shape}"
            self.v_winds = v_winds
        
        if uwind_path and vwind_path:
            self.winds = np.sqrt(np.square(u_winds) + np.square(v_winds))

        self.localize()


    def retrieve_data(self, path, name):
        
        fh = Dataset(path, mode='r')
        
        year = int(path.split('.')[-2])
        lons = fh.variables['lon'][:].data
        lats = fh.variables['lat'][:].data
        times = fh.variables['time'][:].data
        times = times - times[0]
        
        data = fh.variables[name][:].data
        
        if name == 'hgt':
            return (year, times, lats, lons, data)
        else:
            return (year,data)

    
    def localize(self,lat0=20,lat1=70,lon0=220,lon1=340): # Default US localization
        
        lat_mask = ((self.lats>=lat0) & (self.lats<=lat1)) 
        self.loc_lats = self.lats[lat_mask]

        lon_mask = ((self.lons>=lon0) & (self.lons<=lon1)) 
        self.loc_lons = self.lons[lon_mask]

        start_lat = np.argwhere(lat_mask).min()
        end_lat = np.argwhere(lat_mask).max()

        start_lon = np.argwhere(lon_mask).min()
        end_lon = np.argwhere(lon_mask).max()
        
        self.loc_hgts = self.hgts[:,:,start_lat:end_lat+1,start_lon:end_lon+1]

        if self.uwind_path:
            self.loc_u_winds = self.u_winds[:,:,start_lat:end_lat+1,start_lon:end_lon+1]
        if self.vwind_path:
            self.loc_v_winds = self.v_winds[:,:,start_lat:end_lat+1,start_lon:end_lon+1]
        if self.uwind_path and self.vwind_path:
            self.loc_winds = np.sqrt(np.square(self.loc_u_winds) + np.square(self.loc_v_winds))
    

    def plot(self, data, day, level, loc=True, contours=5, figsize=(20,15), cmap='YlOrRd'):
        '''
        INPUT:
            data: hgts, uwnd, vwnd, wnd, all
            day: 0-365 or (Mon,day)
            level: 1-12
            loc:
            contours: Number of line contours
        '''

        # If day input is (Mon,day) tuple, convert to day
        if isinstance(day,tuple):
            day = self.date_to_day(day)
        
        # Get localized data, if necessary
        if loc:
            hgts = self.loc_hgts[day-1,level-1,:,:]
            if self.uwind_path:
                u_winds = self.loc_u_winds[day-1,level-1,:,:]
            if self.vwind_path:
                v_winds = self.loc_v_winds[day-1,level-1,:,:]
            if self.uwind_path and self.uwind_path:
                winds = self.loc_winds[day-1,level-1,:,:]
            lats = self.loc_lats
            lons = self.loc_lons
        else:
            hgts = self.hgts[day-1,level-1,:,:]
            if self.uwind_path:
                u_winds = self.u_winds[day-1,level-1,:,:]
            if self.vwind_path:
                v_winds = self.v_winds[day-1,level-1,:,:]
            if self.uwind_path and self.uwind_path:
                winds = self.winds[day-1,level-1,:,:]
            lats = self.lats
            lons = self.lons
        
        date = (datetime.datetime(self.year, 1, 1) + datetime.timedelta(day - 1)).strftime(r'%b %d %Y')
        title_str = str(date)+' : Level '+str(level)
        
        # Instantiate single figure and axis object
        if data in ['hgts', 'uwnd', 'vwnd', 'wnd']:
            fig = plt.figure(figsize=figsize)
            ax = fig.add_subplot(1,1,1,projection=ccrs.PlateCarree())
            fig.suptitle(title_str,y=0.75,fontsize=16)
        
        def plot_data(values, title, ax):
            cf = ax.contourf(lons, lats, values, 200, transform=ccrs.PlateCarree(), cmap=cmap)
            ax.coastlines()
            ax.set_title(title)
            fig.colorbar(cf, ax=ax,orientation='horizontal',pad=0.03)
            if contours:
                cs = ax.contour(lons, lats, values, contours, transform=ccrs.PlateCarree())
                ax.clabel(cs,inline=1)

        if data == 'hgts':
            plot_data(hgts,'Geopotential Heights', ax)
        
        elif data == 'uwnd':
            plot_data(u_winds,'U Winds',ax)
        
        elif data == 'vwnd':
            plot_data(v_winds,'V Winds',ax)

        elif data == 'wnd':
            plot_data(winds,'Total Wind',ax)

        # Plot all Data
        else: 
            fig, axes = plt.subplots(1,2, figsize=figsize, subplot_kw={'projection': ccrs.PlateCarree()})
            
            plot_data(hgts,'Geopotential Heights',axes[0])
            axes[0].coastlines()

            plot_data(winds, 'Total Wind Speed', axes[1])
            axes[1].coastlines()

            fig.suptitle(title_str,y=0.5,fontsize=16)

        plt.show()
        


    def day_to_date(self,day, fmt=str):
        '''
        INPUT 
            day(int): 1-365
            fmt(dtype): str, tuple
        OUTPUT date(str/tuple): Mon Day Year / (Mon,Day)
        '''
        dt = datetime.datetime(self.year, 1, 1) + datetime.timedelta(day - 1)
        if fmt == str:
            return dt.strftime(r'%b %d %Y')
        elif fmt == tuple:
            return (dt.month,dt.day)


    def date_to_day(self,date):
        '''
        INPUT date(tuple): (Month,day)
        OUTPUT day(int): 1-365
        '''
        return datetime.datetime(self.year,*date).timetuple().tm_yday