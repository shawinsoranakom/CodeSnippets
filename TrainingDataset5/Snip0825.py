def iterate_function(
    eval_function: Callable[[Any, np.ndarray], np.ndarray],
    function_params: Any,
    nb_iterations: int,
    z_0: np.ndarray,
    infinity: float | None = None,
) -> np.ndarray:

    z_n = z_0.astype("complex64")
    for _ in range(nb_iterations):
        z_n = eval_function(function_params, z_n)
        if infinity is not None:
            np.nan_to_num(z_n, copy=False, nan=infinity)
            z_n[abs(z_n) == np.inf] = infinity
    return z_n
