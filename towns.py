from pprint import pprint
from scipy.cluster.hierarchy import *
from scipy.cluster.vq import kmeans2
import folium
import json
import openrouteservice
import pandas as pd
from folium.plugins import marker_cluster
from openrouteservice.distance_matrix import distance_matrix
from openrouteservice.directions import directions
import matplotlib.pyplot as plt

# # all fine uncomment for new file and etc
client = openrouteservice.Client(key='5b3ce3597851110001cf62488f209e533a5b439d9d9808213c37ec64')

data = pd.read_excel('output.xlsx')
# # data.set_index('town', inplace=True)

# # max locals == 50 coz api
lat = data['lat'][:40]
lon = data['lon'][:40]
town = data['town'][:40]

# finding and saving data about distance
coords = []
for i in range(len(lat)):
    coords.append((lon[i], lat[i]))

# computing distances with api
matrix = distance_matrix(
    client,
    locations=coords,
    metrics=['distance'],
    units='km',
)
# # writing result in json
with open('matrix.json', 'w') as file:
    json.dump(matrix, file)
# saving only distances from distance-matrix
with open('matrix.json', 'r') as file:
    dictData = json.load(file)
# saving json-response in xlsx
dick = pd.DataFrame(dictData['distances'])
dick.to_excel('save.xlsx')

# defining amount of clusters with hierarchy algo but wrong
dist = pd.read_excel('save.xlsx')
sam = linkage(dist, method='single', optimal_ordering=True)  # single == min
de = dendrogram(sam,
                leaf_rotation=90,
                leaf_font_size=6,
                )
plt.show()

# ths is some shit i dont understand
centroid, label = kmeans2(dist, 1, minit='points')
d = single(dist)
z = fcluster(d, 100, criterion='distance')


cluster_1 = []
cluster_2 = []
for n in range(len(label)):
    if label[n] == 0:
        cluster_1.append(n)
    else:
        cluster_2.append(n)

# map
m = folium.Map(location=[56.8502777777778, 53.2169444444444], zoom_start=7)
fg_kot = folium.FeatureGroup(name='Пункты с котельными')
fg_punk = folium.FeatureGroup(name='Пункты с хранением топлива')
# # coord of cluster's centers - non automatic =.=
folium.Marker(location=[56.76694444, 51.93361111], popup='Вавож, д.').add_to(fg_punk)
# folium.Marker(location=[56.1595, 52.5303], popup='Казаково, д.').add_to(fg_punk)

for lat_v, lon_v, town_v in zip(lat, lon, town):
    # folium.Marker(location=[lat, lon], popup=town).add_to(marker_cluster)
    folium.Marker(location=(lat_v, lon_v), popup=town_v, icon=folium.Icon(color='green')).add_to(fg_kot)

style = {'fillColor': 'None', 'color': 'black', 'weight': '1', 'fillOpacity': 0.5}  # setting for style_function
with open('new.json', 'r', encoding="utf-8") as read_file:
    state_geo = json.load(read_file)
# полигоны и маркеры из json (райoны)
folium.GeoJson(state_geo, name='Районы', style_function=lambda x: style).add_to(m)
coords_1 = []
coords_2 = []
# # # setting lon lat for routing
for i in range(len(lat)):
    if i in cluster_1:
        coords_1.append((lon[i], lat[i]))
    else:
        coords_2.append((lon[i], lat[i]))

# output is vavozkiy state
# # # routes 40 requests to api per minute so comment/uncomment loops
fg_routes = folium.FeatureGroup(name='Маршруты')  # featuregroup of routes
style_1 = {'color': 'purple'}  # setting for style_function
go = []
for j in range(len(cluster_1)):
    go.append(-1)
    dirc1 = directions(client, [[51.93361111, 56.76694444], coords_1[j]], format_out='geojson', radiuses=[go[j], go[j]])  # 52.5303, 56.1595
    folium.features.GeoJson(data=dirc1, name='Маршруты', style_function=lambda x: style_1).add_to(fg_routes)  # 53.00027778, 57.96694444

# got = []
# for k in range(len(cluster_2)):
#     got.append(-1)
#     dirc2 = directions(client, [[51.93361111, 56.76694444], coords_2[k]], format_out='geojson', radiuses=[got[k], got[k]])
#     folium.features.GeoJson(data=dirc2, name='Маршруты', style_function=lambda x: style_1).add_to(m)

# # Choropleth map of foresting
d = pd.read_csv("forest.csv")
with open("new.json", 'r', encoding="utf-8") as read_file:
    state = json.load(read_file)

chor = folium.Choropleth(geo_data=state, data=d,
                         columns=['name', 'val'],
                         key_on='feature.properties.name',
                         fill_color='PuBuGn',
                         bins=[0, 10, 20, 30, 40, 50, 60, 70, 80],
                         highlight=True,
                         legend_name='Лесистость %',
                         name='Лесистость').add_to(m)
chor.geojson.add_child(
    folium.features.GeoJsonTooltip(['name', 'val'], labels=False))

fg_routes.add_to(m)
fg_punk.add_to(m)
fg_kot.add_to(m)
folium.LayerControl(collapsed=False).add_to(m)

# # saving map data in html
m.save('map.html')
