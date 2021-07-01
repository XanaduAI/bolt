import numpy as np
import math


def _smart_matrix_product(A, B, structure):
    return np.dot(A, B)


def _onenorm(A):
    return np.linalg.norm(A, 1)


class _ExpmPadeHelper:
    """
    Help lazily evaluate a matrix exponential.
    The idea is to not do more work than we need for high expm precision,
    so we lazily compute matrix powers and store or precompute
    other properties of the matrix.
    """

    def __init__(self, A, use_exact_onenorm=False):
        """
        Initialize the object.
        Parameters
        ----------
        A : a dense or sparse square numpy matrix or ndarray
            The matrix to be exponentiated.
        structure : str, optional
            A string describing the structure of matrix `A`.
            Only `upper_triangular` is currently supported.
        use_exact_onenorm : bool, optional
            If True then only the exact one-norm of matrix powers and products
            will be used. Otherwise, the one-norm of powers and products
            may initially be estimated.
        """
        self.A = A
        self._A2 = None
        self._A4 = None
        self._A6 = None
        self._A8 = None
        self._A10 = None
        self._d4_exact = None
        self._d6_exact = None
        self._d8_exact = None
        self._d10_exact = None
        self._d4_approx = None
        self._d6_approx = None
        self._d8_approx = None
        self._d10_approx = None
        self.ident = np.eye(A.shape[0], A.shape[1], dtype=A.dtype)
        self.structure = None
        self.use_exact_onenorm = use_exact_onenorm

    @property
    def A2(self):
        if self._A2 is None:
            self._A2 = _smart_matrix_product(self.A, self.A, structure=self.structure)
        return self._A2

    @property
    def A4(self):
        if self._A4 is None:
            self._A4 = _smart_matrix_product(self.A2, self.A2, structure=self.structure)
        return self._A4

    @property
    def A6(self):
        if self._A6 is None:
            self._A6 = _smart_matrix_product(self.A4, self.A2, structure=self.structure)
        return self._A6

    @property
    def A8(self):
        if self._A8 is None:
            self._A8 = _smart_matrix_product(self.A6, self.A2, structure=self.structure)
        return self._A8

    @property
    def A10(self):
        if self._A10 is None:
            self._A10 = _smart_matrix_product(self.A4, self.A6, structure=self.structure)
        return self._A10

    @property
    def d4_tight(self):
        if self._d4_exact is None:
            self._d4_exact = _onenorm(self.A4) ** (1 / 4.0)
        return self._d4_exact

    @property
    def d6_tight(self):
        if self._d6_exact is None:
            self._d6_exact = _onenorm(self.A6) ** (1 / 6.0)
        return self._d6_exact

    @property
    def d8_tight(self):
        if self._d8_exact is None:
            self._d8_exact = _onenorm(self.A8) ** (1 / 8.0)
        return self._d8_exact

    @property
    def d10_tight(self):
        if self._d10_exact is None:
            self._d10_exact = _onenorm(self.A10) ** (1 / 10.0)
        return self._d10_exact

    @property
    def d4_loose(self):
        return self.d4_tight

    @property
    def d6_loose(self):
        return self.d6_tight

    @property
    def d8_loose(self):
        return self.d8_tight

    @property
    def d10_loose(self):
        return self.d10_tight

    def pade3(self):
        b = (120.0, 60.0, 12.0, 1.0)
        U = _smart_matrix_product(self.A, b[3] * self.A2 + b[1] * self.ident, structure=self.structure)
        V = b[2] * self.A2 + b[0] * self.ident
        return U, V

    def pade5(self):
        b = (30240.0, 15120.0, 3360.0, 420.0, 30.0, 1.0)
        U = _smart_matrix_product(self.A, b[5] * self.A4 + b[3] * self.A2 + b[1] * self.ident, structure=self.structure)
        V = b[4] * self.A4 + b[2] * self.A2 + b[0] * self.ident
        return U, V

    def pade7(self):
        b = (17297280.0, 8648640.0, 1995840.0, 277200.0, 25200.0, 1512.0, 56.0, 1.0)
        U = _smart_matrix_product(
            self.A, b[7] * self.A6 + b[5] * self.A4 + b[3] * self.A2 + b[1] * self.ident, structure=self.structure
        )
        V = b[6] * self.A6 + b[4] * self.A4 + b[2] * self.A2 + b[0] * self.ident
        return U, V

    def pade9(self):
        b = (17643225600.0, 8821612800.0, 2075673600.0, 302702400.0, 30270240.0, 2162160.0, 110880.0, 3960.0, 90.0, 1.0)
        U = _smart_matrix_product(
            self.A,
            (b[9] * self.A8 + b[7] * self.A6 + b[5] * self.A4 + b[3] * self.A2 + b[1] * self.ident),
            structure=self.structure,
        )
        V = b[8] * self.A8 + b[6] * self.A6 + b[4] * self.A4 + b[2] * self.A2 + b[0] * self.ident
        return U, V

    def pade13_scaled(self, s):
        b = (
            64764752532480000.0,
            32382376266240000.0,
            7771770303897600.0,
            1187353796428800.0,
            129060195264000.0,
            10559470521600.0,
            670442572800.0,
            33522128640.0,
            1323241920.0,
            40840800.0,
            960960.0,
            16380.0,
            182.0,
            1.0,
        )
        B = self.A * 2 ** -s
        B2 = self.A2 * 2 ** (-2 * s)
        B4 = self.A4 * 2 ** (-4 * s)
        B6 = self.A6 * 2 ** (-6 * s)
        U2 = _smart_matrix_product(B6, b[13] * B6 + b[11] * B4 + b[9] * B2, structure=self.structure)
        U = _smart_matrix_product(B, (U2 + b[7] * B6 + b[5] * B4 + b[3] * B2 + b[1] * self.ident), structure=self.structure)
        V2 = _smart_matrix_product(B6, b[12] * B6 + b[10] * B4 + b[8] * B2, structure=self.structure)
        V = V2 + b[6] * B6 + b[4] * B4 + b[2] * B2 + b[0] * self.ident
        return U, V


def expm(A):
    # Core of expm, separated to allow testing exact and approximate
    # algorithms.

    h = _ExpmPadeHelper(A, use_exact_onenorm=True)

    # Try Pade order 3.
    eta_1 = max(h.d4_loose, h.d6_loose)
    if eta_1 < 1.495585217958292e-002 and _ell(h.A, 3) == 0:
        U, V = h.pade3()
        return _solve_P_Q(U, V)

    # Try Pade order 5.
    eta_2 = max(h.d4_tight, h.d6_loose)
    if eta_2 < 2.539398330063230e-001 and _ell(h.A, 5) == 0:
        U, V = h.pade5()
        return _solve_P_Q(U, V)

    # Try Pade orders 7 and 9.
    eta_3 = max(h.d6_tight, h.d8_loose)
    if eta_3 < 9.504178996162932e-001 and _ell(h.A, 7) == 0:
        U, V = h.pade7()
        return _solve_P_Q(U, V)
    if eta_3 < 2.097847961257068e000 and _ell(h.A, 9) == 0:
        U, V = h.pade9()
        return _solve_P_Q(U, V)

    # Use Pade order 13.
    eta_4 = max(h.d8_loose, h.d10_loose)
    eta_5 = min(eta_3, eta_4)
    theta_13 = 4.25

    # Choose smallest s>=0 such that 2**(-s) eta_5 <= theta_13
    if eta_5 == 0:
        # Nilpotent special case
        s = 0
    else:
        s = max(int(np.ceil(np.log2(eta_5 / theta_13))), 0)
    s = s + _ell(2 ** -s * h.A, 13)
    U, V = h.pade13_scaled(s)
    X = _solve_P_Q(U, V)
    for i in range(s):
        X = X.dot(X)
    return X


def _solve_P_Q(U, V, structure=None):
    """
    A helper function for expm_2009.
    Parameters
    ----------
    U : ndarray
        Pade numerator.
    V : ndarray
        Pade denominator.
    structure : str, optional
        A string describing the structure of both matrices `U` and `V`.
        Only `upper_triangular` is currently supported.
    Notes
    -----
    The `structure` argument is inspired by similar args
    for theano and cvxopt functions.
    """
    P = U + V
    Q = -U + V
    return np.linalg.solve(Q, P)


def _ell(A, m):
    """
    A helper function for expm_2009.
    Parameters
    ----------
    A : linear operator
        A linear operator whose norm of power we care about.
    m : int
        The power of the linear operator
    Returns
    -------
    value : int
        A value related to a bound.
    """
    # The c_i are explained in (2.2) and (2.6) of the 2005 expm paper.
    # They are coefficients of terms of a generating function series expansion.
    choose_2m_m = math.comb(2 * m, m)
    abs_c_recip = float(choose_2m_m) * float(math.factorial(2 * m + 1))

    # This is explained after Eq. (1.2) of the 2009 expm paper.
    # It is the "unit roundoff" of IEEE double precision arithmetic.
    u = 2 ** -53

    # Compute the one-norm of matrix power p of abs(A).
    A_abs_onenorm = _onenorm_matrix_power_nnm(abs(A), 2 * m + 1)

    # Treat zero norm as a special case.
    if not A_abs_onenorm:
        return 0

    alpha = A_abs_onenorm / (_onenorm(A) * abs_c_recip)
    log2_alpha_div_u = np.log2(alpha / u)
    value = int(np.ceil(log2_alpha_div_u / (2 * m)))
    return max(value, 0)


def _onenorm_matrix_power_nnm(A, p):
    """
    Compute the 1-norm of a non-negative integer power of a non-negative matrix.
    Parameters
    ----------
    A : a square ndarray or matrix or sparse matrix
        Input matrix with non-negative entries.
    p : non-negative integer
        The power to which the matrix is to be raised.
    Returns
    -------
    out : float
        The 1-norm of the matrix power p of A.
    """
    # check input
    if int(p) != p or p < 0:
        raise ValueError("expected non-negative integer p")
    p = int(p)
    if len(A.shape) != 2 or A.shape[0] != A.shape[1]:
        raise ValueError("expected A to be like a square matrix")

    # Explicitly make a column vector so that this works when A is a
    # numpy matrix (in addition to ndarray and sparse matrix).
    v = np.ones((A.shape[0], 1), dtype=float)
    M = A.T
    for i in range(p):
        v = M.dot(v)
    return np.max(v)
