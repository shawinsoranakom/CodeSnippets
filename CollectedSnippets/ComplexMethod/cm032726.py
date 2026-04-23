def _to_order_list(x):
                if x is None:
                    return []
                if isinstance(x, str):
                    return [s.strip() for s in x.split(",") if s.strip()]
                if isinstance(x, (list, tuple)):
                    return [str(s).strip() for s in x if str(s).strip()]
                return []