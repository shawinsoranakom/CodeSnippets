def wrapper(f: F) -> F:
            return gather_metrics(
                name=name,
                func=f,
            )