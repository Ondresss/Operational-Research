import folium
from folium.plugins import AntPath

from VrpGe import  VrpGe
import osmnx as ox
import matplotlib
matplotlib.use('Qt5Agg')
def visualize_interactive_map(vrp, individual):
    """
    Vytvoří interaktivní HTML mapu s reálnými cestami po Ostravě,
    číslovanými zastávkami a animací směru jízdy.
    """
    # 1. Inicializace mapy (střed podle depa)
    # Používáme 'CartoDB positron', aby se předešlo chybě 403 z OpenStreetMap
    depo = vrp.nodes[0]
    m = folium.Map(
        location=[depo.lat, depo.lon],
        zoom_start=12,
        tiles="CartoDB positron"
    )

    nodes_to_draw = [0] + list(individual.route) + [0]
    G = vrp.travel_data
    total_distance_m = 0

    for i in range(len(nodes_to_draw) - 1):
        u_idx, v_idx = nodes_to_draw[i], nodes_to_draw[i+1]
        node_u, node_v = vrp.nodes[u_idx], vrp.nodes[v_idx]

        try:
            orig = ox.distance.nearest_nodes(G, node_u.lon, node_u.lat)
            dest = ox.distance.nearest_nodes(G, node_v.lon, node_v.lat)
            route = ox.shortest_path(G, orig, dest, weight='length')

            if route:
                path_coords = [[G.nodes[n]['y'], G.nodes[n]['x']] for n in route]

                edge_lengths = ox.routing.route_to_gdf(G, route)['length']
                step_dist = edge_lengths.sum()
                total_distance_m += step_dist
                AntPath(
                    locations=path_coords,
                    dash_array=[1, 10],
                    delay=1000,
                    color='royalblue',
                    pulse_color='white',
                    weight=4,
                    opacity=0.8,
                    tooltip=f"Úsek {i+1}: {u_idx} -> {v_idx} ({step_dist:.0f} m)"
                ).add_to(m)
        except Exception as e:
            folium.PolyLine(
                [[node_u.lat, node_u.lon], [node_v.lat, node_v.lon]],
                color="orange", weight=2, dash_array='5', opacity=0.5
            ).add_to(m)

    # 3. Značka pro DEPO (Ikona domečku)
    folium.Marker(
        location=[depo.lat, depo.lon],
        popup=f"DEPO (Start/Cíl)",
        icon=folium.Icon(color='black', icon='home', prefix='fa')
    ).add_to(m)

    # 4. Značky pro ZÁKAZNÍKY (Číslované podle pořadí v trase)
    for order, node_idx in enumerate(individual.route, start=1):
        node = vrp.nodes[node_idx]

        # Vlastní HTML ikona pro zobrazení čísla pořadí
        icon_html = f"""
            <div style="
                font-family: sans-serif; 
                color: white; 
                background-color: crimson; 
                border-radius: 50%; 
                width: 22px; 
                height: 22px; 
                display: flex; 
                align-items: center; 
                justify-content: center; 
                font-size: 11px; 
                font-weight: bold;
                border: 2px solid white;
                box-shadow: 0 0 3px rgba(0,0,0,0.5);">
                {order}
            </div>"""

        folium.Marker(
            location=[node.lat, node.lon],
            icon=folium.DivIcon(html=icon_html),
            popup=f"Zastávka č. {order}<br>Uzel ID: {node_idx}<br>Demand: {getattr(node, 'demand', 'N/A')}"
        ).add_to(m)

    # 5. Přidání infoboxu s celkovou vzdáleností do rohu
    info_html = f'''
        <div style="position: fixed; bottom: 50px; left: 50px; width: 250px; height: 90px; 
                    background-color: white; border:2px solid grey; z-index:9999; font-size:14px;
                    padding: 10px; border-radius: 6px;">
        <b>VRP Ostrava Result</b><br>
        Fitness (vzdálenost): {individual.fitness:.2f}<br>
        Reálná délka cest: {total_distance_m / 1000:.2f} km<br>
        Počet zastávek: {len(individual.route)}
        </div>
    '''
    m.get_root().html.add_child(folium.Element(info_html))

    # 6. Uložení a dokončení
    output_file = "vrp_final_ostrava.html"
    m.save(output_file)
    print(f"Mapa byla úspěšně vytvořena: {output_file}")
    return m


if __name__ == "__main__":
    alg = VrpGe()
    alg.load("./problem.json")
    alg.run(2000)
    print(alg.best_ind)
    visualize_interactive_map(alg,alg.best_ind)