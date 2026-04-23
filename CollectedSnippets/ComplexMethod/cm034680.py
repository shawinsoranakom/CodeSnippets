def func_17(e: float, t: float, *args):
        i = [process_map[arg] for arg in args]
        tv = process_map[t]
        res = None
        if isinstance(tv, str):
            if tv == "window.performance.now":
                current_time = time.time_ns()
                elapsed_ns = current_time - int(start_time * 1e9)
                res = (elapsed_ns + random.random()) / 1e6
            elif tv == "window.Object.create":
                res = OrderedMap()
            elif tv == "window.Object.keys":
                if isinstance(i[0], str) and i[0] == "window.localStorage":
                    res = [
                        "STATSIG_LOCAL_STORAGE_INTERNAL_STORE_V4",
                        "STATSIG_LOCAL_STORAGE_STABLE_ID",
                        "client-correlated-secret",
                        "oai/apps/capExpiresAt",
                        "oai-did",
                        "STATSIG_LOCAL_STORAGE_LOGGING_REQUEST",
                        "UiState.isNavigationCollapsed.1",
                    ]
            elif tv == "window.Math.random":
                res = random.random()
        elif callable(tv):
            res = tv(*i)
        process_map[e] = res