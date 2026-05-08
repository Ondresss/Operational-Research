import  numpy as np
import  math

from scipy.stats import norm
from pip._internal.utils import logging


class InelasticTruss:
    def __init__(self, nodes, elements, fixed_dofs, allowable_stress=235e6):
        self.nodes = np.array(nodes)
        self.elements = elements
        self.fixed_dofs = fixed_dofs
        self.allowable_stress = allowable_stress

        self.names = []
        self.mus = []
        self.areas = []
    def truss_stiffness(self, nodes, elements, areas, E):
        nnode = len(nodes)
        ndof = 2 * nnode
        K = np.zeros((ndof, ndof))
        lengths = np.zeros(len(elements))
        cos_sin = np.zeros((len(elements), 2))

        for e, (i, j) in enumerate(elements):
            xi, yi = nodes[i]
            xj, yj = nodes[j]
            dx = xj - xi
            dy = yj - yi
            L = math.sqrt(dx * dx + dy * dy)
            lengths[e] = L

            c = dx / L
            s = dy / L
            cos_sin[e, :] = [c, s]
            k_val = (E * areas[e] / L)
            k_local = k_val * np.array([
                [ c*c,  c*s, -c*c, -c*s],
                [ c*s,  s*s, -c*s, -s*s],
                [-c*c, -c*s,  c*c,  c*s],
                [-c*s, -s*s,  c*s,  s*s]
            ])

            dof_map = [2*i, 2*i+1, 2*j, 2*j+1]
            for a in range(4):
                for b in range(4):
                    K[dof_map[a], dof_map[b]] += k_local[a, b]

        return K, lengths, cos_sin
    def apply_bcs_and_solve(self,K, f, fixed_dofs):
        ndof = K.shape[0]
        free = np.setdiff1d(np.arange(ndof), fixed_dofs)
        Kff = K[np.ix_(free, free)]
        ff = f[free]
        u = np.zeros(ndof)
        u_free = np.linalg.solve(Kff, ff)
        u[free] = u_free
        return u
    def element_aXial_stress(self,e, nodes, elements, u, E, areas, cos, lengths):
        i, j = elements[e]
        dof_map = [2*i, 2*i+1, 2*j, 2*j+1]
        ui = u[dof_map]
        c, s = cos[e]
        L = lengths[e]
        B = np.array([-c, -s, c, s]) / L
        axial_strain = B.dot(ui)
        axial_stress = E * axial_strain
        return axial_stress
    def limit_state(self,x):
        values = {self.names[i]: x[i] for i in range(len(self.names))}

        if 'E' in self.names:
            E_val = values['E']
        else:
            E_val = self.mus[0]

        random_x = {'E': E_val, 'loads': []}

        for name, val in values.items():
            if name.startswith('P_'):
                parts = name.split('_')
                try:
                    dof = int(parts[-1])
                    random_x['loads'].append((dof, val))
                except Exception:
                    print(f"Could not parse load name: {name}")

        stresses, _ = self.evaluate_performance(self.areas, random_x)

        member_index = np.argmax(np.abs(stresses))
        g = self.allowable_stress - abs(stresses[member_index])
        return g
    def evaluate_performance(self, areas, random_x):
        K, lengths, cos_sin = self.truss_stiffness(self.nodes, self.elements, areas, random_x['E'])

        f = np.zeros(len(self.nodes) * 2)
        for dof, val in random_x['loads']:
            f[dof] = val

        u = self.apply_bcs_and_solve(K, f, self.fixed_dofs)

        stresses = []
        for e in range(len(self.elements)):
            s = self.element_aXial_stress(e, self.nodes, self.elements, u,
                                          random_x['E'], self.areas,cos_sin, lengths)
            stresses.append(s)

        return np.array(stresses), u

    def compute_g_and_grad_X(self, X, limit_state_fun, eps_grad=1e-4):
        n = len(X)

        g0 = limit_state_fun(X)

        grad = np.zeros(n)
        h = eps_grad

        for i in range(n):
            Xp = X.copy()
            Xm = X.copy()

            Xp[i] += h
            Xm[i] -= h

            grad[i] = (limit_state_fun(Xp) - limit_state_fun(Xm)) / (2 * h)

        return g0, grad

    def form_hlrf(self,limit_state_fun, X_mu, X_sigma, tol=1e-3, maX_iter=40, eps_grad=1e-3):
        n = len(X_mu)
        u = np.zeros(n)
        for _ in range(maX_iter):
            X = X_mu + X_sigma * u
            g, grad_X = self.compute_g_and_grad_X(X,limit_state_fun)
            grad_u = grad_X * X_sigma
            norm_grad_u = np.linalg.norm(grad_u)
            if norm_grad_u == 0:
                beta = np.inf if g > 0 else -np.inf
                pf = 0.0 if g > 0 else 1.0
                return beta, pf, X, u
            u_new = - (g / norm_grad_u) * (grad_u / norm_grad_u)
            if np.linalg.norm(u_new - u) < tol:
                u = u_new
                break
            u = u_new
        beta = np.linalg.norm(u)
        pf = norm.cdf(-beta)
        X_star = X_mu + X_sigma * u

        return beta, pf, X_star, u

    def fosm_beta(self,limit_state_fun, x_mu, x_sigma, eps=1e-6):
        n = len(x_mu)
        g0 = limit_state_fun(x_mu)
        grad = np.zeros(n)
        for i in range(n):
            xp = x_mu.copy(); xm = x_mu.copy()
            xp[i] += eps; xm[i] -= eps
            grad[i] = (limit_state_fun(xp) - limit_state_fun(xm)) / (2*eps)
        denom = np.sqrt(np.sum((grad * x_sigma)**2))
        if denom == 0:
            return (np.inf if g0 > 0 else -np.inf), 0.0
        beta = g0 / denom
        pf = norm.cdf(-beta)
        return beta, pf

    @staticmethod
    def generate_truss(n_panels=10, height=1.0, length=10.0, pattern='pratt', top_flat=True):

        dx = length / n_panels
        nodes = []
        elements = []

        for i in range(n_panels + 1):
            nodes.append([i * dx, 0.0])

        if top_flat:
            for i in range(n_panels + 1):
                nodes.append([i * dx, height])
        else:
            for i in range(n_panels + 1):
                y = height if i % 2 == 0 else height * 0.6
                nodes.append([i * dx, y])

        nodes = np.array(nodes)
        for i in range(n_panels):
            elements.append((i, i + 1))

        # top chord
        top_offset = n_panels + 1
        for i in range(n_panels):
            elements.append((top_offset + i, top_offset + i + 1))

        for i in range(n_panels + 1):
            elements.append((i, top_offset + i))

        for i in range(n_panels):
            if pattern.lower() == 'pratt':
                if i % 2 == 0:
                    elements.append((i, top_offset + i + 1))
                else:
                    elements.append((i + 1, top_offset + i))
            elif pattern.lower() == 'howe':
                if i % 2 == 0:
                    elements.append((top_offset + i, i + 1))
                else:
                    elements.append((top_offset + i + 1, i))
            else:
                raise ValueError("pattern must be 'pratt' or 'howe'")

        return nodes, elements
