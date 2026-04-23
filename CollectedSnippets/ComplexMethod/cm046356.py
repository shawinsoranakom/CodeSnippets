def _get_ray_search_alg_kind(search_alg):
    """Return the normalized Ray Tune search algorithm kind for known searcher objects.

    Args:
        search_alg (str | ray.tune.search.Searcher): The search algorithm to identify. Can be None, a string, or a Ray
            Tune searcher object.

    Returns:
        str | None: The normalized search algorithm name, or None if not recognized.
    """
    if search_alg is None:
        return None
    if isinstance(search_alg, str):
        normalized = search_alg.strip().lower()
        return normalized or None

    cls = search_alg.__class__
    module, name = cls.__module__, cls.__name__
    if name == "AxSearch" and module.startswith("ray.tune.search.ax"):
        return "ax"
    if name == "TuneBOHB" and module.startswith("ray.tune.search.bohb"):
        return "bohb"
    if name == "ZOOptSearch" and module.startswith("ray.tune.search.zoopt"):
        return "zoopt"
    return None