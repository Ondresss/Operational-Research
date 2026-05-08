from VrpGe import  VrpGe
import osmnx as ox
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import networkx as nx
import contextily as ctx
from shapely.geometry import LineString
import pandas as pd
import geopandas as gpd

def visualize_gui_real_map(vrp, individual):
    trips = []
    current_trip = [0]
    vehicle_capacity = vrp.vehicle_properties['capacity']
    current_capacity = vehicle_capacity

    for customer_id in individual.route:
        demand = vrp.nodes[customer_id].demand
        if current_capacity < demand:
            current_trip.append(0)
            trips.append(current_trip)
            current_trip = [0, customer_id]
            current_capacity = vehicle_capacity - demand
        else:
            current_trip.append(customer_id)
            current_capacity -= demand
    current_trip.append(0)
    trips.append(current_trip)

    fig, ax = plt.subplots(figsize=(12, 8))

    cmap = plt.get_cmap('tab10')

    for i, trip in enumerate(trips):
        line_coords = []
        for node_id in trip:
            node = vrp.nodes[node_id]
            line_coords.append((node.lon, node.lat))

        df_trip = pd.DataFrame({'geometry': [LineString(line_coords)]})
        gdf_trip = gpd.GeoDataFrame(df_trip, crs="EPSG:4326").to_crs(epsg=3857)

        color = cmap(i % 10)
        gdf_trip.plot(ax=ax, color=color, linewidth=2.5, alpha=0.8, label=f'Okruh {i+1}')

    df_nodes = pd.DataFrame({
        'lon': [n.lon for n in vrp.nodes],
        'lat': [n.lat for n in vrp.nodes],
        'type': ['Depo'] + ['Zákazník'] * (len(vrp.nodes) - 1)
    })
    gdf_nodes = gpd.GeoDataFrame(df_nodes, geometry=gpd.points_from_xy(df_nodes.lon, df_nodes.lat), crs="EPSG:4326").to_crs(epsg=3857)

    gdf_nodes[gdf_nodes['type'] == 'Depo'].plot(ax=ax, color='black', marker='s', markersize=120, zorder=5, label='Depo')
    gdf_nodes[gdf_nodes['type'] == 'Zákazník'].plot(ax=ax, color='red', markersize=30, zorder=4, alpha=0.6)

    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)

    ax.set_axis_off()
    plt.title(f"VRP Ostrava - Celkem {len(trips)} barevně odlišených okruhů")
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.tight_layout()

    plt.show()



if __name__ == "__main__":
    alg = VrpGe()
    alg.load("./problem.json")
    alg.run(2000)
    visualize_gui_real_map(alg,alg.best_ind)