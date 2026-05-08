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
        used_vehicles = 1
        current_capacity = vehicle_properties['capacity']
        previous_customer = 0

        for i in range(len(self.route)):
            current_customer = self.route[i]
            customer_demand = nodes[current_customer].demand

            if current_capacity < customer_demand:

                total_dist += graph[previous_customer][0]['distance']
                total_dist += graph[0][current_customer]['distance']
                current_capacity = vehicle_properties['capacity'] - customer_demand
                used_vehicles += 1
            else:
                total_dist += graph[previous_customer][current_customer]['distance']
                current_capacity -= customer_demand

            previous_customer = current_customer

        total_dist += graph[previous_customer][0]['distance']


        VEHICLE_COST = 2000.0
        OVERLIMIT_PENALTY = 100000.0
        max_vehicles = vehicle_properties['count']

        vehicle_penalty = used_vehicles * VEHICLE_COST
        if used_vehicles > max_vehicles:
            vehicle_penalty += (used_vehicles - max_vehicles) * OVERLIMIT_PENALTY

        self.fitness = total_dist + vehicle_penalty


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







