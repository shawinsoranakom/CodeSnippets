def check_symmetric(array, *, tol=1e-10, raise_warning=True, raise_exception=False):
    """Make sure that array is 2D, square and symmetric.

    If the array is not symmetric, then a symmetrized version is returned.
    Optionally, a warning or exception is raised if the matrix is not
    symmetric.

    Parameters
    ----------
    array : {ndarray, sparse matrix}
        Input object to check / convert. Must be two-dimensional and square,
        otherwise a ValueError will be raised.

    tol : float, default=1e-10
        Absolute tolerance for equivalence of arrays. Default = 1E-10.

    raise_warning : bool, default=True
        If True then raise a warning if conversion is required.

    raise_exception : bool, default=False
        If True then raise an exception if array is not symmetric.

    Returns
    -------
    array_sym : {ndarray, sparse matrix}
        Symmetrized version of the input array, i.e. the average of array
        and array.transpose(). If sparse, then duplicate entries are first
        summed and zeros are eliminated.

    Examples
    --------
    >>> import numpy as np
    >>> from sklearn.utils.validation import check_symmetric
    >>> symmetric_array = np.array([[0, 1, 2], [1, 0, 1], [2, 1, 0]])
    >>> check_symmetric(symmetric_array)
    array([[0, 1, 2],
           [1, 0, 1],
           [2, 1, 0]])
    >>> from scipy.sparse import csr_array
    >>> sparse_symmetric_array = csr_array(symmetric_array)
    >>> check_symmetric(sparse_symmetric_array)
    <Compressed Sparse Row sparse array of dtype 'int64'
        with 6 stored elements and shape (3, 3)>
    """
    if (array.ndim != 2) or (array.shape[0] != array.shape[1]):
        raise ValueError(
            "array must be 2-dimensional and square. shape = {0}".format(array.shape)
        )

    if sp.issparse(array):
        diff = array - array.T
        # only csr, csc, and coo have `data` attribute
        if diff.format not in ["csr", "csc", "coo"]:
            diff = diff.tocsr()
        symmetric = np.all(abs(diff.data) < tol)
    else:
        symmetric = np.allclose(array, array.T, atol=tol)

    if not symmetric:
        if raise_exception:
            raise ValueError("Array must be symmetric")
        if raise_warning:
            warnings.warn(
                (
                    "Array is not symmetric, and will be converted "
                    "to symmetric by average with its transpose."
                ),
                stacklevel=2,
            )
        if sp.issparse(array):
            conversion = "to" + array.format
            array = getattr(0.5 * (array + array.T), conversion)()
        else:
            array = 0.5 * (array + array.T)

    return array