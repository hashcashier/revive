from scipy.optimize import linprog, minimize, fmin_slsqp
import numpy as np

from cvxopt import matrix, spmatrix, solvers


def generate_transaction_set(channel_balances):
    deltas = averaging_deltas(channel_balances)
    linear_prog_solution = solve_rebalance(deltas, channel_balances)
    transactions = linear_program_solution_to_transactions(deltas, channel_balances, linear_prog_solution)
    return transactions


def averaging_deltas(channel_balances):
    deltas = {}
    for contract in channel_balances:
        deposits_left, deposits_right, state, _ = channel_balances[contract][1:]
        credits_left, credits_right = state[0][:2]
        balance_left, balance_right = deposits_left + credits_left, deposits_right + credits_right
        target = (balance_left + balance_right)/2

        deltas[contract] = balance_left - target

    return deltas


def solve_rebalance(deltas, channel_balances):
    n = len(deltas)
    c = [-1.0]*n

    idx_map = address_index_map(channel_balances)

    A = [[0]*n]*len(idx_map)*2
    b = [1e-6*((-1)**x) for x in range(0, len(A))]
    bounds = [(0, abs(deltas[contract])) for contract in deltas]

    for x, contract in enumerate(deltas):
        transfer_limit = deltas[contract]
        addresses = channel_balances[contract][0]
        L, R = idx_map[addresses[0]], idx_map[addresses[1]]
        if transfer_limit < 0:
            # R -> L
            A[2*L][x], A[2*L+1][x] = 1, -1
            A[2*R][x], A[2*R+1][x] = -1, 1
        elif transfer_limit > 0:
            # L -> R
            A[2*L][x], A[2*L+1][x] = -1, 1
            A[2*R][x], A[2*R+1][x] = 1, -1

    return linprog(c=c, A_ub=A, b_ub=b, bounds=bounds)

"""
def solve_rebalance_quad(deltas_out, deltas_in):
    n = len(deltas_in)
    objective = lambda f: -sum([x**2.0 for x in f])
    objective_deriv = lambda dfx: np.array([-2.0*x for x in dfx])
    objective_hess = lambda ddfx: np.array([-2.0 for x in ddfx])
    symmetry_cons = [{'type': 'eq',
                      'fun': lambda x: x[i*n +j] + x[j*n + i],
                      'jac': lambda x: np.array([1.0 if p*n + q == i*n + j or q*n + p == j*n + i else 0.0 for p in range(0, n) for q in range(0, n)])
                      } for i in range(0, n) for j in range(i+1, n)]
    conserve_cons = [{'type': 'eq',
                      'fun': lambda x: np.array(sum(x[i*n:i*n+n])),
                      'jac': lambda x: np.array([1.0 if p*n + q >= i*n and p*n + q < i*n + n else 0.0 for p in range(0, n) for q in range(0, n)])
                      } for i in range(0, n)]
    transfer_bounds = [(-min(deltas_in[i][j], deltas_out[j][i]), min(deltas_out[i][j], deltas_in[j][i])) for i in range(0, n) for j in range(0, n)]
    return minimize(fun=objective,
                    #x0=np.zeros(n*n),
                    x0=np.array([0,.5,-.5,  -.5,0,.5,  .5, -.5, 0]),
                    jac=objective_deriv,
                    hess=objective_hess,
                    bounds=transfer_bounds,
                    constraints=symmetry_cons+conserve_cons,
                    method='COBYLA',
                    options={'disp': True})


def solve_rebalance_extended(deltas_in, deltas_out):
    n = len(deltas_in)
    m = (n*(n-1))//2
    id = spmatrix(1.0, range(m), range(m))
    P = id*-2.0
    q = matrix([0.]*m)
    G = matrix([id, -1.0*id])
    h = matrix(
        [min(deltas_out[i][j], deltas_in[j][i]) for i in range(0, n) for j in range(i+1, n)] +
        [-min(deltas_in[i][j], deltas_out[j][i]) for i in range(0, n) for j in range(i+1, n)])
    C = np.zeros((m, n))
    k = 0
    for i in range(0, n):
        for j in range(i+1, n):
            C[i][k] = 1.
            C[j][k] = -1.
            k = k + 1
    A = matrix(C).trans()
    b = matrix([0.]*n)
    return solvers.qp(P, q, G, h, A, b)
"""

def address_index_map(channel_balances):
    idx_map = {}
    for contract in channel_balances:
        addresses = channel_balances[contract][0]
        for address in addresses:
            if address in idx_map:
                continue
            idx_map[address] = len(idx_map)
    return idx_map


def linear_program_solution_to_transactions(deltas, channel_balances, linear_program):
    print(linear_program['x'])
    transactions = []
    for i, contract in enumerate(deltas):
        transfer_limit = deltas[contract]
        state = channel_balances[contract][3][0]
        last_round = channel_balances[contract][4]
        new_state = None
        if transfer_limit < 0:
            # R -> L
            new_state = (state[0] + int(linear_program['x'][i]), state[1] - int(linear_program['x'][i]), *state[2:])
        elif transfer_limit > 0:
            # L -> R
            new_state = (state[0] - int(linear_program['x'][i]), state[1] + int(linear_program['x'][i]), *state[2:])
        if new_state:
            transactions.append((contract, last_round+1, *new_state))
    print("TRANSACTIONS FROM LINEAR PROGRAM: ")
    print(transactions)
    return transactions
