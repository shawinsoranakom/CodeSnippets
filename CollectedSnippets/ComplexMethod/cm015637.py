def fn(x):
            t = x.size(0) >= 10
            f = x.size(0) >= 100
            if any([]) or any([f]) or any([f, f]):
                return x - 1
            if all([f]) or all([t, f]) or all([f, t]) or all([f, f]):
                return x - 2
            if not (all([]) and all([t]) and all([t, t])):
                return x - 3
            if not (any([t]) and any([t, f]) and any([f, t])):
                return x - 4
            return x + 1