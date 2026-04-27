import random
import copy
import networkx as nx
import osmnx as ox
import json

from Customer import Customer
from Depot import Depot
from Population import Individual, Population


class VrpGe:
    def __init__(self):
        self.nodes = []
        self.graph = nx.Graph()
        self.real_nodes = []
        print("Downloading ox Czech data..")
        self.travel_data = ox.graph_from_place("Ostrava, Czech Republic", network_type="drive")
        print("Done downloading ox Czech data..")
        self.vehicle_properties = {}
        self.population = Population()
        self.best_ind = None

    def load(self, filename):
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for d in data['depots']:
            self.nodes.append(Depot(d['id'], d['lat'], d['lon'], d['service'], d['time_window'], d['demand']))
        for c in data['customers']:
            self.nodes.append(Customer(c['id'], c['lat'], c['lon'], c['service'], c['time_window'], c['demand']))
        self.vehicle_properties['speed'] = data['vehicles']['speed']
        self.vehicle_properties['count'] = data['vehicles']['count']
        self.vehicle_properties['capacity'] = data['vehicles']['capacity']
        print(f"Num of nodes: {len(self.nodes)}")

    @staticmethod
    def _uv(e):
        t = tuple(e)
        if len(t) != 2:
            return None
        return t[0], t[1]

    def eax(self, parent_a: Individual, parent_b: Individual):
        edges_a = self._get_edge_set(parent_a)
        edges_b = self._get_edge_set(parent_b)

        ab_cycles = self._find_ab_cycles(edges_a, edges_b)

        if not ab_cycles:
            return copy.deepcopy(parent_a)

        child_edges = self._edge_exchange(edges_a, edges_b, ab_cycles)
        child_edges = self._fix_degree(child_edges)
        child_edges = self._break_cycles(child_edges)
        child_edges = self._reconnect(child_edges)
        return self._edges_to_individual(child_edges, parent_a)
    def _get_edge_set(self, individual: Individual) -> set:
        edges = set()
        for route in individual.routes:
            if not route:
                continue
            prev = 0
            for node in route:
                if prev != node:
                    edges.add(frozenset({prev, node}))
                prev = node
            if prev != 0:
                edges.add(frozenset({prev, 0}))
        return edges

    def _find_ab_cycles(self, edges_a: set, edges_b: set) -> list:
        only_a = edges_a - edges_b
        only_b = edges_b - edges_a

        if not only_a or not only_b:
            return []

        G = nx.MultiGraph()
        for e in only_a:
            uv = self._uv(e)
            if uv:
                G.add_edge(uv[0], uv[1], owner='A')
        for e in only_b:
            uv = self._uv(e)
            if uv:
                G.add_edge(uv[0], uv[1], owner='B')

        ab_cycles = []
        visited_edges = set()

        for start in list(G.nodes()):
            while True:
                a_edge = None
                for nbr, key_dict in G.adj[start].items():
                    for key, data in key_dict.items():
                        eid = (min(start, nbr), max(start, nbr), key)
                        if data['owner'] == 'A' and eid not in visited_edges:
                            a_edge = (start, nbr, key)
                            break
                    if a_edge:
                        break

                if not a_edge:
                    break

                cycle_edges = []
                current = start
                target_owner = 'A'
                stuck = False

                while True:
                    found = None
                    for nbr, key_dict in G.adj[current].items():
                        for key, data in key_dict.items():
                            eid = (min(current, nbr), max(current, nbr), key)
                            if data['owner'] == target_owner and eid not in visited_edges:
                                found = (current, nbr, key, data['owner'])
                                break
                        if found:
                            break

                    if not found:
                        stuck = True
                        break

                    u, v, key, owner = found
                    eid = (min(u, v), max(u, v), key)
                    visited_edges.add(eid)
                    cycle_edges.append((u, v, owner))
                    current = v
                    target_owner = 'B' if target_owner == 'A' else 'A'

                    if current == start and target_owner == 'A':
                        ab_cycles.append(cycle_edges)
                        break

                if stuck:
                    u, v, key = a_edge
                    visited_edges.add((min(u, v), max(u, v), key))

        return ab_cycles


    def _edge_exchange(self, edges_a: set, edges_b: set, ab_cycles: list) -> set:
        child_edges = set(edges_a)
        chosen_cycle = random.choice(ab_cycles)

        for u, v, owner in chosen_cycle:
            edge = frozenset({u, v})
            if owner == 'A':
                child_edges.discard(edge)
            else:
                child_edges.add(edge)

        return child_edges

    def _fix_degree(self, edges: set) -> set:
        while True:
            loops = {e for e in edges if self._uv(e) is None}
            if loops:
                edges -= loops
                continue
            degree = {}
            for e in edges:
                u, v = self._uv(e)
                degree[u] = degree.get(u, 0) + 1
                degree[v] = degree.get(v, 0) + 1

            bad_nodes = [n for n, d in degree.items() if d > 2]
            if not bad_nodes:
                break

            node = bad_nodes[0]
            incident = [e for e in edges if node in e]

            def edge_dist(e):
                uv = self._uv(e)
                if uv and self.graph.has_edge(uv[0], uv[1]):
                    return self.graph[uv[0]][uv[1]]['distance']
                return 0.0

            worst = max(incident, key=edge_dist)
            edges.discard(worst)

        return edges

    def _break_cycles(self, edges: set) -> set:
        G = nx.Graph()
        for e in edges:
            uv = self._uv(e)
            if uv:
                G.add_edge(uv[0], uv[1])

        def edge_dist(u, v):
            if self.graph.has_edge(u, v):
                return self.graph[u][v]['distance']
            return 0.0

        for comp in list(nx.connected_components(G)):
            sub = G.subgraph(comp)
            if all(sub.degree(n) >= 2 for n in comp):
                worst = max(sub.edges(), key=lambda e: edge_dist(e[0], e[1]))
                edges.discard(frozenset(worst))

        return edges

    def _reconnect(self, edges: set) -> set:
        def rebuild_graph():
            G = nx.Graph()
            for e in edges:
                uv = self._uv(e)
                if uv:
                    G.add_edge(uv[0], uv[1])
            for i in range(len(self.nodes)):
                if i not in G:
                    G.add_node(i)
            return G

        G = rebuild_graph()

        while True:
            comps = list(nx.connected_components(G))
            if len(comps) <= 1:
                break

            comp_endpoints = []
            for comp in comps:
                endpoints = [n for n in comp if G.degree(n) <= 1]
                if not endpoints:
                    endpoints = list(comp)
                comp_endpoints.append((comp, endpoints))

            best, best_dist = None, float('inf')
            for i in range(len(comp_endpoints)):
                for j in range(i + 1, len(comp_endpoints)):
                    for u in comp_endpoints[i][1]:
                        for v in comp_endpoints[j][1]:
                            if self.graph.has_edge(u, v):
                                d = self.graph[u][v]['distance']
                                if d < best_dist:
                                    best_dist, best = d, (u, v)

            if best is None:
                for i in range(len(comp_endpoints)):
                    for j in range(i + 1, len(comp_endpoints)):
                        if comp_endpoints[i][1] and comp_endpoints[j][1]:
                            best = (comp_endpoints[i][1][0], comp_endpoints[j][1][0])
                            break
                    if best:
                        break
                if best is None:
                    break

            u, v = best
            edges.add(frozenset({u, v}))
            edges = self._fix_degree(edges)
            G = rebuild_graph()

        return edges

    def _edges_to_individual(self, edges: set, fallback: Individual) -> Individual:
        G = nx.Graph()
        for e in edges:
            uv = self._uv(e)
            if uv: G.add_edge(uv[0], uv[1])

        if 0 not in G: G.add_node(0)

        visited_nodes = {0}
        all_routes = []

        starts = list(G.neighbors(0))
        for s in starts:
            if s in visited_nodes:
                continue

            route = []
            curr = s
            prev = 0

            while curr != 0 and curr not in visited_nodes:
                visited_nodes.add(curr)
                route.append(curr)

                next_nodes = [n for n in G.neighbors(curr) if n != prev]
                if not next_nodes:
                    break

                prev = curr
                curr = next_nodes[0]

            if route:
                all_routes.append(route)

        all_customer_ids = set(range(1, len(self.nodes)))
        missing = all_customer_ids - visited_nodes

        for node in missing:
            if all_routes:
                all_routes[0].append(node)
            else:
                all_routes.append([node])

        return Individual(routes=all_routes, fitness=0)

    def run(self, iterations):
        self.fillNodes()
        self.fillEdges()

        pop_size = 200
        self.population.init_population(pop_size, len(self.nodes) - 1, self.vehicle_properties['count'])
        for ind in self.population.population:
            ind.calculate_fitness(self.nodes, self.vehicle_properties, self.graph)

        best_fitness = float('inf')
        no_improve = 0

        for current_iter in range(iterations):
            offspring_size = 50
            new_children = []

            for _ in range(offspring_size):
                p1 = self.get_parent()
                p2 = self.get_parent()
                child = self.eax(p1, p2)
                if random.random() < 0.3:
                    child = self._mutate(child)

                child.calculate_fitness(self.nodes, self.vehicle_properties, self.graph)
                new_children.append(child)
            combined = self.population.population + new_children
            combined.sort(key=lambda x: x.fitness)
            self.population.population = combined[:pop_size]

            current_best = self.population.population[0].fitness
            if current_best < best_fitness:
                best_fitness = current_best
                self.best_ind = self.population.population[0]
                no_improve = 0
                print(f"Iterace {current_iter}: NOVÝ REKORD = {best_fitness:.2f}")
            else:
                no_improve += 1

            if no_improve >= 150:
                self._restart_population()
                no_improve = 0
                print(f"  >> Restart populace v iteraci {current_iter}")

            if current_iter % 10 == 0:
                print(f"Iterace {current_iter}: Best Fitness = {best_fitness:.2f}")

        print(self.best_ind)

    def _mutate(self, individual: Individual) -> Individual:
        child = copy.deepcopy(individual)
        non_empty = [i for i, r in enumerate(child.routes) if len(r) >= 2]
        if not non_empty:
            return child

        if random.random() < 0.8:
            idx = random.choice(non_empty)
            route = child.routes[idx]
            i, j = sorted(random.sample(range(len(route)), 2))
            route[i:j + 1] = reversed(route[i:j + 1])
        else:
            src = random.choice(non_empty)
            others = [i for i in range(len(child.routes)) if i != src]
            if others:
                dst = random.choice(others)
                cust = child.routes[src].pop(random.randrange(len(child.routes[src])))
                child.routes[dst].insert(random.randrange(len(child.routes[dst]) + 1), cust)

        return child

    def _restart_population(self):
        self.population.population.sort(key=lambda x: x.fitness)
        elite_n = max(5, len(self.population.population) // 10)
        elite = self.population.population[:elite_n]

        new_inds = []
        n_cust = len(self.nodes) - 1
        n_veh = self.vehicle_properties['count']
        cap = self.vehicle_properties['capacity']

        for _ in range(len(self.population.population) - elite_n):
            perm = list(range(1, n_cust + 1))
            random.shuffle(perm)
            routes, cur, load = [], [], 0
            for c in perm:
                d = self.nodes[c].demand
                if load + d > cap and cur:
                    routes.append(cur)
                    cur, load = [c], d
                else:
                    cur.append(c)
                    load += d
            if cur:
                routes.append(cur)
            while len(routes) < n_veh:
                routes.append([])
            ind = Individual(routes=routes[:n_veh], fitness=0)
            ind.calculate_fitness(self.nodes, self.vehicle_properties, self.graph)
            new_inds.append(ind)

        self.population.population = elite + new_inds


    def get_parent(self):
        candidates = random.sample(self.population.population, 3)
        return min(candidates, key=lambda x: x.fitness)

    def fillNodes(self):
        for i in range(len(self.nodes)):
            self.graph.add_node(i, data=self.nodes[i])
        self.getActualNodes()

    def getActualNodes(self):
        for node in self.nodes:
            target_node = ox.distance.nearest_nodes(self.travel_data, node.lon, node.lat)
            self.real_nodes.append(target_node)

    def fillEdges(self):
        print("Creating full mesh graph")
        num_nodes = len(self.real_nodes)
        for i in range(num_nodes):
            for j in range(num_nodes):
                if i == j:
                    self.graph.add_edge(i, i, distance=0.0, travel_time=0.0)
                    continue
                try:
                    dist_m = nx.shortest_path_length(
                        self.travel_data, self.real_nodes[i], self.real_nodes[j], weight='length'
                    )
                    dist_km = dist_m / 1000.0
                    time_min = (dist_km / self.vehicle_properties['speed']) * 60
                    self.graph.add_edge(i, j, distance=dist_km, travel_time=time_min)
                except nx.NetworkXNoPath:
                    print(f"No path: {i} -> {j}")
        print(f"Graph ready. Nodes: {len(self.graph.nodes)}, Edges: {len(self.graph.edges)}")