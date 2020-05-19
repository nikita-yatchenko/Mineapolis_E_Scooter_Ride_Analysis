"""
Author: Nikita Yatchenko
Date: May 18 2020
"""
from itertools import count

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

### Get scooter data for September and October from http://opendata.minneapolismn.gov/
sept_data = pd.read_csv('https://opendata.arcgis.com/datasets/deb23b7c4983427aa83881db0e5ee6ad_0.csv')
oct_data = pd.read_csv('https://opendata.arcgis.com/datasets/70977c11cc9b419fa5856351be721fbd_0.csv')
nov_data = pd.read_csv('https://opendata.arcgis.com/datasets/01cc4e6abf5f40398efc299585dc9775_0.csv')

scooter_data = pd.concat([sept_data, oct_data, nov_data], join='outer')
scooter_data = scooter_data[scooter_data.EndCenterlineID.map(len) < 10]
scooter_data['EndCenterlineID'] = scooter_data['EndCenterlineID'].astype('float64').astype('int64')
scooter_data.sort_values(by='StartTime', inplace=True)
scooter_data.StartTime = pd.to_datetime(scooter_data.StartTime) - pd.Timedelta(hours=5)
### Get GBSID (http://opendata.minneapolismn.gov/) street identification and Merge with Scooter
gbsid = pd.read_csv('https://opendata.arcgis.com/datasets/43b425de3d4f444f96a5bf6605e3081b_3.csv', usecols=['GBSID','STREET_F_N', 'STREET_O_N'])
gbsid.drop_duplicates(subset='GBSID', keep='first', inplace=True)
gbsid.dropna(subset = ['STREET_F_N', 'STREET_O_N'], inplace = True)
gbsid['intersection'] = gbsid.STREET_O_N.str.cat(gbsid.STREET_F_N, sep=' and ')

scooter_street_data = pd.merge(scooter_data, gbsid, how = 'left', left_on = 'EndCenterlineID', right_on = 'GBSID')
scooter_street_data.dropna(subset=['intersection'], inplace=True)
scooter_street_data.StartTime= pd.to_datetime(scooter_street_data.StartTime)
####
### Obtain avg. # of trips per hour for every day
scoot_group_daily = scooter_street_data.groupby(by = 'StartTime')['TripID', 'intersection'].agg({'TripID' : 'count', 'intersection': lambda x: x.value_counts().index[0]})
scoot_group_daily['StartTime'] = scoot_group_daily.index
scoot_group_daily.rename(columns={'TripID':'NumberTrips'}, inplace=True)
scoot_group_daily['StartTimeH'] = scoot_group_daily.StartTime.astype('str').str.split(' ', expand = True)[1]

### Then obtain avg. # of trips per hour and the most frequent destination for the day
scoot_group_hourly = scoot_group_daily.groupby(by = 'StartTimeH')['NumberTrips', 'intersection'].agg({'NumberTrips' : 'mean', 'intersection': lambda x: x.value_counts().index[0]})
scoot_group_hourly.sort_values(by='StartTimeH', inplace=True)

### Interactive Plot
fig, ax = plt.subplots(figsize=(15,7))
ax.plot(scoot_group_hourly.index, scoot_group_hourly.NumberTrips, color = 'steelblue', marker = 'o', markerfacecolor='salmon', picker = 10)
ax.set_ylim(-5, 300)
plt.xticks(rotation=45)
plt.xticks(np.arange(0, len(scoot_group_hourly.index), 2.0))
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.xlabel('Hours')
plt.ylabel('Average Number of E-Scooter Rides')
ax.set_title('Hourly Average Number of E-Scooter Rides for September - November in Minneapolis, MN, USA', fontsize = 14)
plt.text(0, 250, 'Most Common Destination at {} hours is {}'.format(scoot_group_hourly.index[0], scoot_group_hourly.intersection[0]))


### Adding interactivity
def onpick(event):
    if not (not ax.collections):
        print(ax.collections)
        for dot in ax.collections:
            dot.remove()
    selection = event.ind[0]
    new_x = [0] * len(scoot_group_hourly.index)
    new_x[selection] = selection
    new_y = [-10] * len(scoot_group_hourly.index)
    new_y[selection] = scoot_group_hourly.iloc[selection, 0]
    ax.scatter(new_x, new_y, color = 'red', s = 40, zorder = 4, marker = 's')


    print(selection)
    pick = [scoot_group_hourly.index[selection], scoot_group_hourly.iloc[selection, 1]]
    ax.texts[0].remove()
    plt.text(0, 250, 'Most Common Destination at {} hours is {}'.format(pick[0], pick[1]))

fig.canvas.mpl_connect('pick_event', onpick)
