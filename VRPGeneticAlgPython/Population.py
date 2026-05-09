from typing import List

import networkx as nx
import  numpy as np
from Depot import  Depot
from Customer import Customer


class Individual:
    def __init__(self,route,fitness):
        self.route = route
        self.fitness = fitness
    def get_edges(self):
        edges = set()
        for i in range(len(self.route) - 1):
            edge = tuple(sorted((self.route[i], self.route[i+1])))
            edges.add(edge)

        last_edge = tuple(sorted((self.route[-1], self.route[0])))
        edges.add(last_edge)

        return edges


    def getIndividualFromGraph(self, G, no_customers):
        all_required = set(range(1, no_customers+1))

        xor_route = []
        visited_in_dfs = set()
        for node in G.nodes:
            if node not in visited_in_dfs:
                comp_nodes = list(nx.dfs_preorder_nodes(G, source=node))
                for n in comp_nodes:
                    if n != 0 and n not in visited_in_dfs:
                        xor_route.append(n)
                        visited_in_dfs.add(n)

        already_in_route = set(xor_route)
        missing = [n for n in all_required if n not in already_in_route]
        if missing:
            xor_route.extend(missing)
        self.route = xor_route


    def calculate_fitness(self, nodes, vehicle_properties, graph):
        total_dist = 0.0
        time_penalty = 0.0
        used_vehicles = 1

        TIME_WINDOW_PENALTY = 2000.0
        VEHICLE_COST = 50000.0
        OVERLIMIT_PENALTY = 10000000.0

        capacity = vehicle_properties['capacity']
        current_capacity = capacity
        current_time = nodes[0].start_time
        previous_customer = 0

        for customer_idx in self.route:
            customer = nodes[customer_idx]

            travel_dist = graph[previous_customer][customer_idx]['distance']
            travel_time = graph[previous_customer][customer_idx]['travel_time']

            if current_capacity < customer.demand:
                total_dist += graph[previous_customer][0]['distance']
                used_vehicles += 1
                current_capacity = capacity

                previous_customer = 0
                current_time = nodes[0].start_time

            current_capacity -= customer.demand
            total_dist += travel_dist
            current_time += travel_time

            if current_time < customer.start_time:
                current_time = customer.start_time
            elif current_time > customer.end_time:
                time_penalty += (current_time - customer.end_time) * TIME_WINDOW_PENALTY

            current_time += customer.service_time
            previous_customer = customer_idx

        total_dist += graph[previous_customer][0]['distance']
        current_time += graph[previous_customer][0]['travel_time']

        depot = nodes[0]
        if current_time > depot.end_time:
            time_penalty += (current_time - depot.end_time) * TIME_WINDOW_PENALTY

        max_vehicles = vehicle_properties['count']
        vehicle_penalty = used_vehicles * VEHICLE_COST
        if used_vehicles > max_vehicles:
            vehicle_penalty += (used_vehicles - max_vehicles) * OVERLIMIT_PENALTY

        self.fitness = total_dist + vehicle_penalty + time_penalty


    def __str__(self):
        return f"Individual:  {self.route} \nFitness:: {self.fitness})"

    def copy(self):
        return Individual(self.route,self.fitness)


class Population:
    def __init__(self):
        self.population : List[Individual] = []
    def create_random_individual(self,num_customers):
        random_route = list(range(1,num_customers+1))
        np.random.shuffle(random_route)
        return Individual(random_route,0)

    def init_population(self,population_size,num_customers):
        for i in range(0,population_size):
            self.population.append(self.create_random_individual(num_customers))







