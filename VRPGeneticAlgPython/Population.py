from typing import List
import  numpy as np
class Individual:
    def __init__(self,routes,fitness):
        self.routes = routes
        self.fitness = fitness
    def get_edges(self):
        edges = set()
        for route in self.routes:
            for index in range(0,len(route)-1):
                u = route[index]
                v = route[index+1]
                edge = tuple(sorted([u,v]))
                edges.add(edge)
        return edges
    def calculate_fitness(self, nodes, vehicle_properties, graph):
        total_dist = 0.0
        total_load_penalty = 0.0
        total_time_penalty = 0.0

        VEHICLE_COST = 2000.0
        OVERLIMIT_VEHICLE_PENALTY = 100000.0
        W_TIME = 50.0

        capacity_limit = vehicle_properties['capacity']
        max_vehicles = vehicle_properties['count']
        depot = nodes[0]

        all_sub_routes = []
        for route in self.routes:
            temp = []
            for node_id in route:
                if node_id == 0:
                    if temp:
                        all_sub_routes.append(temp)
                        temp = []
                else:
                    temp.append(node_id)
            if temp:
                all_sub_routes.append(temp)

        num_vehicles = len(all_sub_routes)
        vehicle_usage_penalty = num_vehicles * VEHICLE_COST

        if num_vehicles > max_vehicles:
            vehicle_usage_penalty += (num_vehicles - max_vehicles) * OVERLIMIT_VEHICLE_PENALTY

        for route in all_sub_routes:
            current_load = 0
            current_time = float(depot.start_time)
            prev_node = 0

            for node_id in route:
                edge_data = graph[prev_node][node_id]
                total_dist += edge_data['distance']
                current_time += edge_data['travel_time']

                customer = nodes[node_id]

                if current_time < customer.start_time:
                    current_time = customer.start_time

                if current_time > customer.end_time:
                    total_time_penalty += (current_time - customer.end_time)

                current_time += customer.service_time
                current_load += customer.demand
                prev_node = node_id

            return_edge = graph[prev_node][0]
            total_dist += return_edge['distance']
            current_time += return_edge['travel_time']

            if current_time > depot.end_time:
                total_time_penalty += (current_time - depot.end_time)

            if current_load > capacity_limit:
                total_load_penalty += (current_load - capacity_limit) * 1000.0

        self.fitness = (total_dist +
                        vehicle_usage_penalty +
                        total_load_penalty +
                        (total_time_penalty * W_TIME))


    def __str__(self):
        return f"Individual:  {self.routes} \nFitness:: {self.fitness})"

    def copy(self):
        return Individual(self.routes,self.fitness)


class Population:
    def __init__(self):
        self.population : List[Individual] = []
    def create_random_individual(self,num_customers, num_vehicles):
        customers = list(range(1, num_customers))
        np.random.shuffle(customers)
        routes = [[] for _ in range(num_vehicles)]
        for i, customer_idx in enumerate(customers):
            vehicle_idx = i % num_vehicles
            routes[vehicle_idx].append(customer_idx)
        final_individual = []
        for r in routes:
            full_route = [0] + r + [0]
            final_individual.append(full_route)
        return Individual(final_individual,0)

    def init_population(self,population_size,num_customers,num_vehicles):
        for i in range(0,population_size):
            self.population.append(self.create_random_individual(num_customers,num_vehicles))







