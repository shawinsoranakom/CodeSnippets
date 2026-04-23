def create_wrapper(**kwargs):
            params = kwargs.pop("params") if "params" in kwargs else None
            state = kwargs.pop("state") if "state" in kwargs else None
            if params and state:
                variables = {**params, **state}
            elif params:
                variables = params
            elif state:
                variables = state
            else:
                variables = None
            kwargs["variables"] = variables
            flax_model = flax_model_class()
            if flax_model_method:
                kwargs["method"] = getattr(flax_model, flax_model_method)
            return FlaxLayer(flax_model_class(), **kwargs)