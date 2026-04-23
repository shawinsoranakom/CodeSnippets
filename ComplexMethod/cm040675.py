def result(self):
        if not self.built:
            raise ValueError(
                "Cannot get result() since the metric has not yet been built."
            )
        results = {}
        unique_name_counters = {}
        for mls in self._flat_metrics:
            if not mls:
                continue
            for m in mls.metrics:
                name = m.name
                if mls.output_name:
                    name = f"{mls.output_name}_{name}"
                if name not in unique_name_counters:
                    results[name] = m.result()
                    unique_name_counters[name] = 1
                else:
                    index = unique_name_counters[name]
                    unique_name_counters[name] += 1
                    name = f"{name}_{index}"
                    results[name] = m.result()

        for mls in self._flat_weighted_metrics:
            if not mls:
                continue
            for m in mls.metrics:
                name = m.name
                if mls.output_name:
                    name = f"{mls.output_name}_{name}"
                if name not in unique_name_counters:
                    results[name] = m.result()
                    unique_name_counters[name] = 1
                else:
                    name = f"weighted_{m.name}"
                    if mls.output_name:
                        name = f"{mls.output_name}_{name}"
                    if name not in unique_name_counters:
                        unique_name_counters[name] = 1
                    else:
                        index = unique_name_counters[name]
                        unique_name_counters[name] += 1
                        name = f"{name}_{index}"
                    results[name] = m.result()
        return results