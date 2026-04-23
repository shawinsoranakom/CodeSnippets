def clear_inf(self, o: Any):
        if isinstance(o, dict):
            return {
                str(k)
                if not isinstance(k, (str, int, float, bool, type(None)))
                else k: self.clear_inf(v)
                for k, v in o.items()
            }
        elif isinstance(o, list):
            return [self.clear_inf(v) for v in o]
        elif isinstance(o, float) and math.isinf(o):
            return "inf"
        return o