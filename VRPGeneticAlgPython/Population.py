from typing import List
import  numpy as np
from Depot import  Depot
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


    def getIndividualFromGraph(self, G,no_customers):
        xor_route = []
        all_customers = list(range(1,no_customers))
        if len(G.nodes) > 0:
            start_nodes = [n for n, d in G.degree() if d == 1]
            start_node = start_nodes[0] if start_nodes else list(G.nodes())[0]

            current_node = start_node
            visited = {current_node}
            xor_route.append(current_node)

            while len(xor_route) < G.number_of_nodes():
                next_node = None
                for neighbor in G.neighbors(current_node):
                    if neighbor not in visited:
                        next_node = neighbor
                        break

                if next_node is not None:
                    visited.add(next_node)
                    xor_route.append(next_node)
                    current_node = next_node
                else:
                    break

        missing_nodes = [n for n in all_customers if n not in visited and n != 0]
        final_tour = xor_route + missing_nodes
        self.route = final_tour



    def calculate_fitness(self, nodes, vehicle_properties, graph):
        total_dist = 0.0
        total_load_penalty = 0.0
        total_time_penalty = 0.0
        vehicle_usage_penalty = 0.0
        VEHICLE_COST = 2000.0
        OVERLIMIT_VEHICLE_PENALTY = 100000.0
        W_TIME = 50.0

        capacity_limit = vehicle_properties['capacity']
        max_vehicles = vehicle_properties['count']
        used_vehicles = 1

        current_time = 0.0
        previous_customer = 0
        for i in range(0,len(self.route)):
            current_customer = self.route[i]
            total_dist += graph[previous_customer][current_customer]['distance']
            current_time += graph[previous_customer][current_customer]['travel_time']

            customer = nodes[current_customer]
            capacity_limit -= customer.demand
            if (capacity_limit <= 0):
                vehicle_usage_penalty += VEHICLE_COST
                capacity_limit = vehicle_properties['capacity']
                used_vehicles += 1

            if current_time < customer.start_time:
                current_time = customer.start_time

            if current_time > customer.end_time:
                total_time_penalty += W_TIME

            current_time += customer.service_time
            previous_customer = current_customer
        total_dist += graph[previous_customer][0]['distance']

        vehicle_usage_penalty = used_vehicles * VEHICLE_COST
        if (used_vehicles > max_vehicles):
            vehicle_usage_penalty += (used_vehicles - max_vehicles) * OVERLIMIT_VEHICLE_PENALTY
        distance_weight = 250.0
        self.fitness = (total_dist * distance_weight +
                        vehicle_usage_penalty +
                        total_load_penalty +
                        (total_time_penalty * W_TIME))


    def __str__(self):
        return f"Individual:  {self.route} \nFitness:: {self.fitness})"

    def copy(self):
        return Individual(self.route,self.fitness)


class Population:
    def __init__(self):
        self.population : List[Individual] = []
    def create_random_individual(self,num_customers):
        random_route = list(range(1,num_customers))
        np.random.shuffle(random_route)
        return Individual(random_route,0)

    def init_population(self,population_size,num_customers):
        for i in range(0,population_size):
            self.population.append(self.create_random_individual(num_customers))







