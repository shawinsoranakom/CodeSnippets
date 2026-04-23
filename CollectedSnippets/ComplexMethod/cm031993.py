def wrapper_function(*args, **kwargs):
            key = str((args, frozenset(kwargs)))
            if key in cache:
                if _cache_info["ttl"] is None or (cache[key][1] + _cache_info["ttl"]) >= time.time():
                    _cache_info["hits"] += 1
                    print(f'Warning, reading cache, last read {(time.time()-cache[key][1])//60} minutes ago'); time.sleep(2)
                    cache[key][1] = time.time()
                    return cache[key][0]
                else:
                    del cache[key]

            result = func(*args, **kwargs)
            cache[key] = [result, time.time()]
            _cache_info["misses"] += 1
            _cache_info["currsize"] += 1

            if _cache_info["currsize"] > _cache_info["maxsize"]:
                oldest_key = None
                for k in cache:
                    if oldest_key is None:
                        oldest_key = k
                    elif cache[k][1] < cache[oldest_key][1]:
                        oldest_key = k
                del cache[oldest_key]
                _cache_info["currsize"] -= 1

            if cache_path is not None:
                with open(cache_path, "wb") as f:
                    pickle.dump(cache, f)

            return result