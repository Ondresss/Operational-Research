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
    clean_routes = [0] + individual.route + [0]

    fig, ax = plt.subplots(figsize=(12, 8))

    colors = ['red', 'blue', 'green', 'purple', 'orange']

    all_lons = [node.lon for node in vrp.nodes]
    all_lats = [node.lat for node in vrp.nodes]

    for i, route in enumerate(clean_routes):
        color = colors[i % len(colors)]
        full_route =  clean_routes

        line_coords = []
        for node_id in full_route:
            node = vrp.nodes[node_id]
            line_coords.append((node.lon, node.lat))


        df = pd.DataFrame({'geometry': [LineString(line_coords)]})
        gdf = gpd.GeoDataFrame(df, crs="EPSG:4326")
        gdf = gdf.to_crs(epsg=3857)
        gdf.plot(ax=ax, color=color, linewidth=2, alpha=0.7, label=f'Auto {i+1}')

    df_nodes = pd.DataFrame({
        'lon': [n.lon for n in vrp.nodes],
        'lat': [n.lat for n in vrp.nodes],
        'type': ['Depo'] + ['Zákazník'] * (len(vrp.nodes) - 1)
    })
    gdf_nodes = gpd.GeoDataFrame(df_nodes, geometry=gpd.points_from_xy(df_nodes.lon, df_nodes.lat), crs="EPSG:4326")
    gdf_nodes = gdf_nodes.to_crs(epsg=3857)

    gdf_nodes[gdf_nodes['type'] == 'Depo'].plot(ax=ax, color='black', marker='s', markersize=100, zorder=5)
    gdf_nodes[gdf_nodes['type'] == 'Zákazník'].plot(ax=ax, color='red', markersize=20, zorder=4)

    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)

    ax.set_axis_off()
    plt.title(f"VRP Ostrava - {len(clean_routes)} aktivních tras")
    plt.legend()

    print("Otevírám GUI okno...")
    plt.show()



if __name__ == "__main__":
    alg = VrpGe()
    alg.load("./problem.json")
    alg.run(2000)
    visualize_gui_real_map(alg,alg.best_ind)