def _param_generator(self, params):
        # Try dict handling; if that fails, treat as sequence
        if hasattr(params, "items"):
            return {k: v.force_bytes for k, v in params.items()}
        else:
            return [p.force_bytes for p in params]