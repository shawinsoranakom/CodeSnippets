def _find_concrete_model_from_proxy(self, proxy_models, model_state):
        for base in model_state.bases:
            if not (isinstance(base, str) or issubclass(base, models.Model)):
                continue
            base_key = make_model_tuple(base)
            base_state = proxy_models.get(base_key)
            if not base_state:
                # Concrete model found, stop looking at bases.
                return base_key
            return self._find_concrete_model_from_proxy(proxy_models, base_state)