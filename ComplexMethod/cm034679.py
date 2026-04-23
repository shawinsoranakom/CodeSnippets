def func_5(e: float, t: float):
        n = process_map[e]
        tres = process_map[t]
        if n is None:
            process_map[e] = tres
        elif is_slice(n):
            nt = n + [tres] if tres is not None else n
            process_map[e] = nt
        else:
            if is_string(n) or is_string(tres):
                res = to_str(n) + to_str(tres)
            elif is_float(n) and is_float(tres):
                res = n + tres
            else:
                res = "NaN"
            process_map[e] = res