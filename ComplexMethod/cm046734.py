def _poll_tqdm():
                    while not _tqdm_monitor_stop.is_set():
                        for bar in list(getattr(_tqdm_cls, "_instances", set())):
                            try:
                                n = bar.n or 0
                                total = bar.total or _total
                                if total > 0 and n > 0:
                                    pct = min(int(n * 100 / total), 100)
                                    progress_callback(
                                        status_message = f"{_desc}... {pct}% ({n:,}/{total:,})"
                                    )
                            except (AttributeError, ReferenceError):
                                pass
                        _tqdm_monitor_stop.wait(3)