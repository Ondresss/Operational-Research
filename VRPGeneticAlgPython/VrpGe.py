import random
import copy
import networkx as nx
import osmnx as ox
import json

from networkx import Graph

from Customer import Customer
from Depot import Depot
from Population import Individual, Population


class   VrpGe:
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


    def eax(self, parent_a: Individual, parent_b: Individual):
        edges_a = parent_a.get_edges()
        edges_b = parent_b.get_edges()

        ab_cycles = self._find_ab_cycles(edges_a, edges_b)
        if not ab_cycles:
            return copy.deepcopy(parent_a)

        child_edges = self._edge_exchange(edges_a, edges_b, ab_cycles)
        G = self._fix_degree(child_edges,edges_a)
        G = self._break_cycles(G)
        G = self._reconnect(G,edges_a)

        ind = Individual([],0)
        ind.getIndividualFromGraph(G,len(self.nodes)-1)
        return ind

    def _find_ab_cycles(self, edges_a: set, edges_b: set) -> list:
        new_edges = edges_a ^ edges_b
        G = nx.Graph()
        for u, v in new_edges:
            parent = 'A' if (u, v) in edges_a or (v, u) in edges_a else 'B'
            G.add_edge(u, v, belongs=parent, visited=False)

        ab_cycles = []

        for start_node in list(G.nodes):
            while True:
                has_available_a = False
                for neighbor in G.neighbors(start_node):
                    if G[start_node][neighbor]['belongs'] == 'A' and not G[start_node][neighbor]['visited']:
                        has_available_a = True
                        break

                if not has_available_a:
                    break

                current_cycle = []
                current_node = start_node
                next_parent = 'A'

                while True:
                    found_next = None
                    for neighbor in G.neighbors(current_node):
                        edge_data = G[current_node][neighbor]
                        if edge_data['belongs'] == next_parent and not edge_data['visited']:
                            found_next = neighbor
                            edge_data['visited'] = True
                            current_cycle.append((current_node, neighbor, next_parent))
                            break

                    if found_next is None:
                        break

                    current_node = found_next
                    next_parent = 'B' if next_parent == 'A' else 'A'

                    if current_node == start_node:
                        ab_cycles.append(current_cycle)
                        break
        return ab_cycles


    def _edge_exchange(self, edges_a: set, edges_b: set, ab_cycles: list) -> set:
        child_edges = set(edges_a)
        chosen_cycle = random.choice(ab_cycles)

        for u, v, owner in chosen_cycle:
            edge = (u,v)
            if owner == 'A':
                child_edges.discard(edge)
            else:
                child_edges.add(edge)

        return child_edges

    def _fix_degree(self, child_edges: set,edges_a : set):

        G = nx.Graph()
        for u,v in child_edges:
            edge = (u,v)
            if edge in edges_a:
                G.add_edge(u,v,belongsA=True)
            else:
                G.add_edge(u,v,belongsA=False)
        nodes_to_fix = [n for n, d in G.degree() if d > 2]

        for current_node in nodes_to_fix:
            while G.degree(current_node) > 2:
                edges = []
                for neigh in G.neighbors(current_node):
                    is_a = G[current_node][neigh]['belongsA']
                    dist = self.graph[current_node][neigh]['distance']
                    edges.append((neigh, is_a, dist))
                edges.sort(key=lambda x: (x[1], x[2]), reverse=True)
                neighbor_to_remove = edges[0][0]
                G.remove_edge(current_node, neighbor_to_remove)

        return G

    def _break_cycles(self, G):
        for component in list(nx.connected_components(G)):
            subgraph = G.subgraph(component)
            try:
                cycle_edges = nx.find_cycle(subgraph)
                max_dist = -1.0
                edge_to_remove = None

                for u, v in cycle_edges:
                    dist = self.graph[u][v]['distance']
                    if dist > max_dist:
                        max_dist = dist
                        edge_to_remove = (u, v)

                if edge_to_remove:
                    G.remove_edge(*edge_to_remove)

            except nx.NetworkXNoCycle:
                continue

        return G


    def _reconnect(self, G,edges_a):
        while nx.number_connected_components(G) > 1:
            components = list(nx.connected_components(G))
            best_edge = None
            min_dist = float('inf')

            for i in range(len(components)):
                for j in range(i + 1, len(components)):
                    for n1 in components[i]:
                        for n2 in components[j]:
                            if not self.graph.has_edge(n1, n2):
                                continue
                            dist = self.graph[n1][n2]['distance']
                            if dist < min_dist:
                                min_dist = dist
                                best_edge = (n1, n2)

            if best_edge:
                u, v = best_edge
                G.add_edge(u, v, belongsA=False, visited=False)
            else:
                break

        return G

    def run(self, iterations,no_pop):
        self.fillNodes()
        self.fillEdges()

        pop_size = no_pop
        self.population.init_population(pop_size, len(self.nodes) - 1)
        for ind in self.population.population:
            ind.calculate_fitness(self.nodes, self.vehicle_properties, self.graph)

        best_fitness = float('inf')

        for current_iter in range(iterations):
            self.population.population.sort(key=lambda x: x.fitness)
            new_population = [self.population.population[0]]

            while len(new_population) < pop_size:
                p1 = self.get_parent()
                p2 = self.get_parent()

                child = self.eax(p1, p2)

                if random.random() < 0.3:
                    child = self._mutate(child)

                child.calculate_fitness(self.nodes, self.vehicle_properties, self.graph)
                new_population.append(child)

            self.population.population = new_population

            current_best_ind = self.population.population[0]
            current_best_fitness = current_best_ind.fitness

            if current_best_fitness < best_fitness:
                best_fitness = current_best_fitness
                self.best_ind = current_best_ind
                print(f"Iteration {current_iter}: NEW BEST FITNESS = {best_fitness:.2f}")

            if current_iter % 10 == 0:
                print(f"Iteration {current_iter}: Best Fitness = {best_fitness:.2f}")

        self.printFinalResult()




    def printFinalResult(self):
        if not self.best_ind:
            print("Best individual wasnt found")
            return

        total_dist_m = 0.0
        route = self.best_ind.route
        previous_node = 0

        current_capacity = self.vehicle_properties['capacity']

        for customer_idx in route:
            customer = self.nodes[customer_idx]

            if current_capacity < customer.demand:
                total_dist_m += self.graph[previous_node][0]['distance']
                previous_node = 0
                current_capacity = self.vehicle_properties['capacity']

            total_dist_m += self.graph[previous_node][customer_idx]['distance']
            current_capacity -= customer.demand
            previous_node = customer_idx

        total_dist_m += self.graph[previous_node][0]['distance']

        print("\n" + "="*30)
        print("Best Individual")
        print("="*30)
        print(f"Trasa: {route}")
        print(f"Fitness: {self.best_ind.fitness:.2f}")
        print(f"Distance: {total_dist_m / 1000:.2f} km ({total_dist_m:.0f} m)")
        print("="*30)



    def _mutate(self, individual: Individual) -> Individual:
        child = copy.deepcopy(individual)

        route = child.route

        if random.random() < 0.8:
            i, j = sorted(random.sample(range(len(route)), 2))
            route[i:j + 1] = reversed(route[i:j + 1])

        else:
            idx_src = random.randrange(len(route))
            cust = route.pop(idx_src)
            idx_dst = random.randrange(len(route) + 1)
            route.insert(idx_dst, cust)

        return child


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
                    dist_m = float(dist_m)
                    speed_m_min = (self.vehicle_properties['speed'] * 1000) / 60
                    time_min = dist_m / speed_m_min

                    self.graph.add_edge(i, j, distance=dist_m, travel_time=time_min)
                except nx.NetworkXNoPath:
                    print(f"No path: {i} -> {j}")
        print(f"Graph ready. Nodes: {len(self.graph.nodes)}, Edges: {len(self.graph.edges)}")