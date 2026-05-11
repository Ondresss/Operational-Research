from InelasticTruss import  InelasticTruss
from DETruss import  DETruss
from Population import Population
from Population import  Material
import  numpy as np

def example_pratt_truss():
    n_panels = 10
    nodes, elements = InelasticTruss.generate_truss(n_panels=n_panels, height=1.0, length=10.0)
    print(elements)
    fixed_dofs = [0, 1, 2 * n_panels + 1]

    allowable_stress = 250e6
    truss = InelasticTruss(nodes, elements, fixed_dofs, allowable_stress=allowable_stress)

    E_mu, E_sigma = 210e9, 0.05 * 210e9
    q_mu, q_sigma = -50000.0, 0.1 * 50000.0

    load_names = [f"P_{2*i + 1}" for i in range(1, n_panels)]

    truss.names = ['E'] + load_names
    truss.mus = np.array([E_mu] + [q_mu] * len(load_names))
    X_sigma = np.array([E_sigma] + [q_sigma] * len(load_names))

    truss.areas = np.full(len(elements), 0.0015)

    ls_fun = truss.limit_state

    print("--- START ---")
    beta, pf, x_star, u_star = truss.form_hlrf(ls_fun, truss.mus, X_sigma)

    print("-" * 30)
    print(f"Index B beta: {beta:.4f}")
    print(f"Propability of failure Pf: {pf:.6e}")
    print("-" * 30)
    print("Critical values:")
    for i, name in enumerate(truss.names):
        print(f"  {name}: {x_star[i]:.2f} (mean is {truss.mus[i]:.2f})")


if __name__ == "__main__":
    n_panels = 10
    nodes, elements = InelasticTruss.generate_truss(n_panels=n_panels, height=1.0, length=10.0)
    fixed_dofs = [0, 1, 2 * n_panels + 1]
    allowable_stress = 250e6
    truss = InelasticTruss(nodes, elements, fixed_dofs, allowable_stress=allowable_stress)
    load_names = [f"P_{2*i + 1}" for i in range(1, n_panels)]
    truss.names = ['E'] + load_names
    E_mu, E_sigma = 210e9, 0.05 * 210e9
    q_mu, q_sigma = -50000.0, 0.1 * 50000.0
    density = 7850
    material = Material(E_mu, E_sigma, q_mu, q_sigma, density)

    pop_size = 20
    no_areas = len(elements)
    min_area = 0.0001
    max_area = 0.01

    population = Population(
        pop_size,
        truss,
        no_areas,
        min_area,
        max_area,
        n_panels,
        material
    )

    solver = DETruss(truss, population)
    print("Start (50 generationfs)...")
    solver.run(no_iter=50, H=6)
    print("Finished.")

    best_ind = population.find_best()

    print("\n" + "="*30)
    print("Results: ")
    print("="*30)
    print(f"Best fitness: {best_ind.fitness:.2f} kg")

    print("\nAreas (m2):")
    print(best_ind.areas)