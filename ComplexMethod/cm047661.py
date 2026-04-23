def _log_ormcache_stats():
        """ Log statistics of ormcache usage by database, model, and method. """
        from odoo.modules.registry import Registry  # noqa: PLC0415
        try:
            # {dbname: {method: StatsLine}}
            cache_stats: defaultdict[str, dict[Callable, StatsLine]] = defaultdict(dict)
            # {dbname: (cache_name, entries, count, total_size)}
            cache_usage: defaultdict[str, list[tuple[str, int, int, int]]] = defaultdict(list)

            # browse the values in cache
            registries = Registry.registries.snapshot
            class_slots = {}
            for i, (dbname, registry) in enumerate(registries.items(), start=1):
                if not check_continue_logging():
                    return
                _logger.info("Processing database %s (%d/%d)", dbname, i, len(registries))
                db_cache_stats = cache_stats[dbname]
                db_cache_usage = cache_usage[dbname]
                for cache_name, cache in registry._Registry__caches.items():
                    cache_total_size = 0
                    for cache_key, cache_value in cache.snapshot.items():
                        method = cache_key[1]
                        stats = db_cache_stats.get(method)
                        if stats is None:
                            stats = db_cache_stats[method] = StatsLine(method, _COUNTERS[dbname, method])
                        stats.nb_entries += 1
                        if not show_size:
                            continue
                        size = get_cache_size((cache_key, cache_value), cache_info=method.__qualname__, class_slots=class_slots)
                        cache_total_size += size
                        stats.sz_entries_sum += size
                        stats.sz_entries_max = max(stats.sz_entries_max, size)
                    db_cache_usage.append((cache_name, len(cache), cache.count, cache_total_size))

            # add counters that have no values in cache
            for (dbname, method), counter in _COUNTERS.copy().items():  # copy to avoid concurrent modification
                if not check_continue_logging():
                    return
                db_cache_stats = cache_stats[dbname]
                stats = db_cache_stats.get(method)
                if stats is None:
                    db_cache_stats[method] = StatsLine(method, counter)

            # Output the stats
            log_msgs = ['Caches stats:']
            size_column_info = (
                f"{'Memory %':>10},"
                f"{'Memory SUM':>12},"
                f"{'Memory MAX':>12},"
            ) if show_size else ''
            column_info = (
                f"{'Cache Name':>25},"
                f"{'Entry':>7},"
                f"{size_column_info}"
                f"{'Hit':>6},"
                f"{'Miss':>6},"
                f"{'Err':>6},"
                f"{'Gen Time [s]':>13},"
                f"{'Hit Ratio':>10},"
                f"{'TX Hit Ratio':>13},"
                f"{'TX Call':>8},"
                "  Method"
            )

            for dbname, db_cache_stats in sorted(cache_stats.items(), key=lambda k: k[0] or '~'):
                if not check_continue_logging():
                    return
                log_msgs.append(f'Database {dbname or "<no_db>"}:')
                log_msgs.extend(
                    f" * {cache_name}: {entries}/{count}{' (' if cache_total_size else ''}{cache_total_size}{' bytes)' if cache_total_size else ''}"
                    for cache_name, entries, count, cache_total_size in db_cache_usage
                )
                log_msgs.append('Details:')

                # sort by -sz_entries_sum and method_name
                db_cache_stat = sorted(db_cache_stats.items(), key=lambda k: (-k[1].sz_entries_sum, k[0].__name__))
                sz_entries_all = sum(stat.sz_entries_sum for _, stat in db_cache_stat)
                log_msgs.append(column_info)
                for method, stat in db_cache_stat:
                    size_data = (
                        f'{stat.sz_entries_sum / (sz_entries_all or 1) * 100:9.1f}%,'
                        f'{stat.sz_entries_sum:12d},'
                        f'{stat.sz_entries_max:12d},'
                    ) if show_size else ''
                    log_msgs.append(
                        f'{stat.counter.cache_name:>25},'
                        f'{stat.nb_entries:7d},'
                        f'{size_data}'
                        f'{stat.counter.hit:6d},'
                        f'{stat.counter.miss:6d},'
                        f'{stat.counter.err:6d},'
                        f'{stat.counter.gen_time:13.3f},'
                        f'{stat.counter.ratio:9.1f}%,'
                        f'{stat.counter.tx_ratio:12.1f}%,'
                        f'{stat.counter.tx_calls:8d},'
                        f'  {method.__qualname__}'
                    )
            _logger.info('\n'.join(log_msgs))
        except Exception:  # noqa: BLE001
            _logger.exception()
        finally:
            global _logger_state  # noqa: PLW0603
            with _logger_lock:
                _logger_state = 'wait'