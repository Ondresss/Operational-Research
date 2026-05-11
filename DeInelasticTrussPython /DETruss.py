import random

from InelasticTruss import  InelasticTruss
from Population import  Population
from Population import  Material
from scipy.stats import norm,cauchy

from Population import Individual
import  numpy as np

class DETruss:
    def __init__(self,truss,population : Population):
        self.truss = truss
        self.population = population
        self.archive = []
    def run(self,no_iter,H):
        self.population.generate_random()
        k = 0
        mcr = [0.5] * H
        mf = [0.5] * H
        current_index = 0
        while current_index < no_iter:
            S_F = []
            S_CR = []
            diff_f = []
            best_ind = self.population.find_best()
            print(f"Start of iteration {current_index} - Current best fitness: {best_ind.fitness}, Current best ind: {best_ind.areas}")
            for i in range(len(self.population.population)):
                ri = random.randint(0, H - 1)
                current_cr = 0
                if mcr[ri] is not None:
                    current_cr = mcr[ri]

                cri = norm.rvs(current_cr, 0.1)
                fi = cauchy.rvs(mf[ri],0.1)
                pi = random.uniform(2/self.population.pop_size,0.2)
                current_individual = self.population.population[i]
                trial_vector = self.calculate_trial_vector(current_individual,fi,pi,cri)
                new_individual = Individual(0.3,self.population.material)
                new_individual.areas = trial_vector
                new_individual.evaluate_fitness(self.population.n_panels,self.population.truss)
                print(f"Current individual - {i} Fitness: {current_individual.fitness},New individual - {i} Fitness: {new_individual.fitness} ")
                if self.select(current_individual, new_individual):
                    self.archive.append(current_individual)
                    if len(self.archive) > self.population.pop_size:
                        self.archive.pop(random.randint(0, len(self.archive) - 1))
                    delta_f = abs(current_individual.fitness - new_individual.fitness)
                    S_F.append(fi)
                    S_CR.append(cri)
                    diff_f.append(delta_f)
                    self.population.population[i] = new_individual
                    print(f"New selected fitness: {new_individual.fitness}")
                if S_F:
                    total_diff = sum(diff_f)
                    weights = [d / total_diff for d in diff_f]

                    mean_cr = sum(w * c for w, c in zip(weights, S_CR))

                    num = sum(w * (f**2) for w, f in zip(weights, S_F))
                    den = sum(w * f for w, f in zip(weights, S_F))
                    mean_f = num / den

                    mf[k] = mean_f
                    mcr[k] = mean_cr

                    k = (k + 1) % H
            best_ind = self.population.find_best()
            print(f"End of iteration {current_index} - Current best fitness: {best_ind.fitness}, Current best ind: {best_ind.areas}")
            current_index+=1

        self.archive = []


    def calculate_trial_vector(self,current_individual : Individual,fi,p_i,cri):
        best_ind = self.population.find_p_best(p_i)

        r1 = self.population.find_random_individuals_except([current_individual])

        combined_pool = self.population.population + self.archive
        r2 = self.find_random_from_pool_except(combined_pool, [current_individual, r1])

        x = np.array(current_individual.areas)
        x_pbest = np.array(best_ind.areas)
        x_r1 = np.array(r1.areas)
        x_r2 = np.array(r2.areas)

        v = x + fi * (x_pbest - x) + fi * (x_r1 - x_r2)
        v_repaired = self.repair_trial_vector(v,current_individual)
        u = current_individual.areas.copy()
        j_rand = random.randint(0, len(u) - 1)
        for i in range(len(u)):
            random_value = random.random()

            if random_value <= cri or i == j_rand:

                u[i] = v_repaired[i]
            else:
                pass

        return u



    def repair_trial_vector(self,v,current_individual : Individual):
        v_new = v.copy()
        for i in range(len(v)):
            x_area = current_individual.areas[i]
            if v[i] < self.population.min:
                v_new[i] = (x_area + self.population.min) / 2
            if v[i] > self.population.max:
                v_new[i] = (x_area + self.population.max) / 2
        return v_new


    def find_random_from_pool_except(self, combined_pool, exceptPool):
        random_ind = random.choice(combined_pool)
        while random_ind in exceptPool:
            random_ind =random.choice(combined_pool)
        return random_ind

    def select(self,current_individual : Individual,new_individual : Individual):
        if new_individual.fitness < current_individual.fitness:

            self.archive.append(current_individual)
            if len(self.archive) > self.population.pop_size:
                self.archive.pop(random.randint(0, len(self.archive) - 1))

            return True
        return False





