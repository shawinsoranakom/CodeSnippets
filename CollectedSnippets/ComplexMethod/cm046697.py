def _monitor_tqdm():
            from tqdm.auto import tqdm as _tqdm_cls

            while not _tqdm_stop.is_set():
                for bar in list(getattr(_tqdm_cls, "_instances", set())):
                    try:
                        n, total = bar.n or 0, bar.total or 0
                        desc = getattr(bar, "desc", "") or ""
                        if total > 0 and n > 0 and desc:
                            pct = min(int(n * 100 / total), 100)
                            _send_status(
                                event_queue, f"{desc.strip()} {pct}% ({n:,}/{total:,})"
                            )
                    except (AttributeError, ReferenceError):
                        pass
                _tqdm_stop.wait(3)