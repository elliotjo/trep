import numpy as np
import numpy.linalg
import scipy as sp
import scipy.linalg

from numpy import dot

def solve_tv_lqr(A, B, Q, R):
    """
    (K, P) = solve_tv_lqr(A, B, Q, R)
    Solve the time-varying discrete LQR problem.

    Inputs:
      A - Sequence of N matrices (system dynamics)
      B - Sequence of N matrices (input matrix)
      Q - Function Q(k) returning state cost at time k
      R - Function R(k) returning input cost at time k

    Returns:
      K - Sequence of N matrices (optimal feedback gain)
      P - matrix (P(0) solution to Ricatti equation)
    """
    
    # Hackish attempt to start with a steady state approximation to P.
    # Slowed down convergence of the cart on a pendulum, so I'm not
    # using it anymore.
    
    ## kf = len(A)
    ## K = [None]*(kf)
    ## P = Q(kf)

    ## k = kf-1
    ## for i in range(500):
    ##     gamma = (R(k) + B[k].T * P * B[k])
    ##     K_part = B[k].T*P*A[k] # See lq function for explanation of this
    ##     K[k] = np.linalg.solve(gamma, K_part)
    ##     P_old = P
    ##     P = Q(k) + A[k].T*P*A[k] - K_part.T*K[k]
    ##     P = (P + P.T)/2.0  # Note: absolutely necessary for stability

    ## print "diff: ", np.linalg.norm(P-P_old)

    kf = len(A)
    K = [None]*(kf)
    P = Q(kf)

    for k in reversed(range(kf)):
        # gamma = (R(k) + B[k].T * P * B[k])
        gamma = R(k) + dot(dot(B[k].T, P),B[k])
        # K_part = B[k].T*P*A[k] 
        K_part = dot(B[k].T,dot(P,A[k])) # See lq function for explanation of this
        K[k] = np.linalg.solve(gamma, K_part)
        # P = Q(k) + A[k].T*P*A[k] - K_part.T*K[k]
        P = Q(k) + dot(dot(A[k].T,P),A[k]) - dot(K_part.T,K[k])
        P = (P + P.T)/2.0  # Note: absolutely necessary for stability

    return (K, P)
        

def solve_tv_lq(A, B, q, r, Q, S, R):
    """
    (K, P) = solve_tv_lqr(A, B, Q, R)
    Solve the time-varying discrete LQR problem.

    Inputs:
      A - Sequence of N matrices (system dynamics)
      B - Sequence of N matrices (input matrix)
      q - Sequence of N+1 matrices of state linear cost
      r - Sequence of N matrices of input linear cost
      Q - Function Q(k) returning state cost at time k
      R - Function R(k) returning input cost at time k
      S - Function S(k) returning cross term cost at time k

    Returns:
      K - Sequence of N matrices (optimal feedback gain)
      C - Sequence of N matrices (affine component of optimal control)
      P - matrix (P(0) solution to Ricatti equation)
      b - matrix (b(0) solution to affine Ricatti equation)
    """
    
    kf = len(A)
    K = [None]*kf
    C = [None]*kf
    P = Q(kf)
    b = q[kf]

    for k in reversed(range(kf)):
        #gamma = R(k) + B[k].T*P*B[k]
        gamma = R(k) + dot(dot(B[k].T,P),B[k])
        gamma_lu = sp.linalg.lu_factor(gamma, True)

        # Pull K_part out so later we can replace K.T*gamma*K with
        # K_part.T*K to avoid numeric instabilities from gamma *
        # inverse(gamma)
        K_part = dot(dot(B[k].T, P),A[k]) + S(k).T
        C[k] = sp.linalg.lu_solve(gamma_lu, dot(B[k].T,b) + r[k])
        K[k] = sp.linalg.lu_solve(gamma_lu, K_part)
        b = q[k] - dot(K[k].T,r[k]) + dot(A[k].T - dot(K[k].T,B[k].T),b)
        P = Q(k) + dot(dot(A[k].T,P),A[k]) - dot(K_part.T,K[k])

        #print "asymm err: ", np.linalg.norm( (P-P.T)/2 )
        P = (P + P.T)/2.0  # Note: absolutely necessary for stability
    return (K, C, P, b)