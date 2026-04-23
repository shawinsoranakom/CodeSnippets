def _get_metadata_for_step(self, *, step_idx, step_params, all_params):
        """Get params (metadata) for step `name`.

        This transforms the metadata up to this step if required, which is
        indicated by the `transform_input` parameter.

        If a param in `step_params` is included in the `transform_input` list,
        it will be transformed.

        Parameters
        ----------
        step_idx : int
            Index of the step in the pipeline.

        step_params : dict
            Parameters specific to the step. These are routed parameters, e.g.
            `routed_params[name]`. If a parameter name here is included in the
            `pipeline.transform_input`, then it will be transformed. Note that
            these parameters are *after* routing, so the aliases are already
            resolved.

        all_params : dict
            All parameters passed by the user. Here this is used to call
            `transform` on the slice of the pipeline itself.

        Returns
        -------
        dict
            Parameters to be passed to the step. The ones which should be
            transformed are transformed.
        """
        if (
            self.transform_input is None
            or not all_params
            or not step_params
            or step_idx == 0
        ):
            # we only need to process step_params if transform_input is set
            # and metadata is given by the user.
            return step_params

        sub_pipeline = self[:step_idx]
        sub_metadata_routing = get_routing_for_object(sub_pipeline)
        # here we get the metadata required by sub_pipeline.transform
        transform_params = {
            key: value
            for key, value in all_params.items()
            if key
            in sub_metadata_routing.consumes(
                method="transform", params=all_params.keys()
            )
        }
        transformed_params = dict()  # this is to be returned
        transformed_cache = dict()  # used to transform each param once
        # `step_params` is the output of `process_routing`, so it has a dict for each
        # method (e.g. fit, transform, predict), which are the args to be passed to
        # those methods. We need to transform the parameters which are in the
        # `transform_input`, before returning these dicts.
        for method, method_params in step_params.items():
            transformed_params[method] = Bunch()
            for param_name, param_value in method_params.items():
                # An example of `(param_name, param_value)` is
                # `('sample_weight', array([0.5, 0.5, ...]))`
                if param_name in self.transform_input:
                    # This parameter now needs to be transformed by the sub_pipeline, to
                    # this step. We cache these computations to avoid repeating them.
                    transformed_params[method][param_name] = _cached_transform(
                        sub_pipeline,
                        cache=transformed_cache,
                        param_name=param_name,
                        param_value=param_value,
                        transform_params=transform_params,
                    )
                else:
                    transformed_params[method][param_name] = param_value
        return transformed_params