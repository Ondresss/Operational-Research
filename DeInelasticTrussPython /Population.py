import math
import  random
from typing import List

from InelasticTruss import  InelasticTruss
import  numpy as np


class Material:
    def __init__(self,E_mu,E_sigma,q_mu,q_sigma,density):
        self.E_mu = E_mu
        self.E_sigma = E_sigma
        self.q_mu = q_mu
        self.q_sigma = q_sigma
        self.density = density

class Individual:
    def __init__(self,reliability_threshold,material : Material):
        self.fitness = 0
        self.areas = []
        self.reliability_threshold = reliability_threshold
        self.material = material
    def init_random(self,no_areas,minL,maxU):
        self.areas = [random.uniform(minL,maxU) for i in range(no_areas)]

    def calculate_distance(self,element,nodes):
        i,j = element
        xi, yi =  nodes[i]
        xj, yj =  nodes[j]
        dx = xj - xi
        dy = yj - yi
        L = math.sqrt(dx * dx + dy * dy)
        return L


    def calculate_weight(self,density,truss : InelasticTruss):
        weight = 0
        elements = truss.elements
        for i in range(len(self.areas)):
            Ai = self.areas[i]
            element = elements[i]
            L = self.calculate_distance(element,truss.nodes)
            mul = Ai * L
            weight += mul
        return weight * density


    def evaluate_fitness(self,n_panels,truss : InelasticTruss):

        truss.mus = np.array([self.material.E_mu] + [self.material.q_mu] * len(truss.names))
        X_sigma = np.array([self.material.E_sigma] + [self.material.q_sigma] * len(truss.names))
        truss.areas = np.array(self.areas).copy()
        ls_fun = truss.limit_state
        beta, pf, x_star, u_star = truss.form_hlrf(ls_fun, truss.mus, X_sigma)

        total_weight = self.calculate_weight(self.material.density,truss)
        cp = 1e6
        beta_target = self.reliability_threshold

        if beta >= beta_target:
            penalty = 0
        else:
            penalty = cp * (beta_target - beta)**2

        self.fitness = total_weight + penalty

class Population:
    def __init__(self,no_individuals,truss : InelasticTruss,no_areas,min,max,n_panels,material : Material):
        self.pop_size = no_individuals
        self.population = []
        self.truss = truss
        self.no_areas = no_areas
        self.min = min
        self.max = max
        self.n_panels = n_panels
        self.material = material

    def generate_random(self):
        for i in range(self.pop_size):
            ind = Individual(3.0,self.material)
            ind.init_random(self.no_areas,self.min,self.max)
            ind.evaluate_fitness(self.n_panels, self.truss)
            self.population.append(ind)

    def find_p_best(self, p_i):
        sorted_pop = sorted(self.population, key=lambda ind: ind.fitness)

        part = sorted_pop[0:int(len(sorted_pop)*p_i)]
        return random.choice(part)
    def find_best(self):
        sorted_population = sorted(self.population, key=lambda ind: ind.fitness)
        return sorted_population[0]

    def find_random_individuals_except(self,except_individuals : List[Individual]):
        found_random = random.choice(self.population)
        while found_random in except_individuals:
            found_random  = random.choice(self.population)
        return found_random



