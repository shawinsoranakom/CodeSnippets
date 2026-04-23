def sync_wrapper(*args: P.args, **kwargs: P.kwargs):
                key = _make_hashable_key(args, kwargs)
                redis_key = _make_redis_key(key, func_name) if shared_cache else ""

                # Fast path: check cache without lock
                if shared_cache:
                    result = _get_from_redis(redis_key)
                    if result is not _MISSING:
                        return result
                else:
                    result = _get_from_memory(key)
                    if result is not _MISSING:
                        return result

                # Slow path: acquire lock for cache miss/expiry
                with cache_lock:
                    # Double-check: another thread might have populated cache
                    if shared_cache:
                        result = _get_from_redis(redis_key)
                        if result is not _MISSING:
                            return result
                    else:
                        result = _get_from_memory(key)
                        if result is not _MISSING:
                            return result

                    # Cache miss - execute function
                    logger.debug(f"Cache miss for {func_name}")
                    result = target_func(*args, **kwargs)

                    # Store result (skip ``None`` if the caller opted out of
                    # caching it — used for transient-error sentinels).
                    if cache_none or result is not None:
                        if shared_cache:
                            _set_to_redis(redis_key, result)
                        else:
                            _set_to_memory(key, result)

                    return result