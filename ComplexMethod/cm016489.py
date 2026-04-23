def execute(self, calc_cond_batch: Callable, model: BaseModel, conds: list[list[dict]], x_in: torch.Tensor, timestep: torch.Tensor, model_options: dict[str]):
        self._model = model
        self.set_step(timestep, model_options)
        context_windows = self.get_context_windows(model, x_in, model_options)
        enumerated_context_windows = list(enumerate(context_windows))

        conds_final = [torch.zeros_like(x_in) for _ in conds]
        if self.fuse_method.name == ContextFuseMethods.RELATIVE:
            counts_final = [torch.ones(get_shape_for_dim(x_in, self.dim), device=x_in.device) for _ in conds]
        else:
            counts_final = [torch.zeros(get_shape_for_dim(x_in, self.dim), device=x_in.device) for _ in conds]
        biases_final = [([0.0] * x_in.shape[self.dim]) for _ in conds]

        for callback in comfy.patcher_extension.get_all_callbacks(IndexListCallbacks.EXECUTE_START, self.callbacks):
            callback(self, model, x_in, conds, timestep, model_options)

        for enum_window in enumerated_context_windows:
            results = self.evaluate_context_windows(calc_cond_batch, model, x_in, conds, timestep, [enum_window], model_options)
            for result in results:
                self.combine_context_window_results(x_in, result.sub_conds_out, result.sub_conds, result.window, result.window_idx, len(enumerated_context_windows), timestep,
                                            conds_final, counts_final, biases_final)
        try:
            # finalize conds
            if self.fuse_method.name == ContextFuseMethods.RELATIVE:
                # relative is already normalized, so return as is
                del counts_final
                return conds_final
            else:
                # normalize conds via division by context usage counts
                for i in range(len(conds_final)):
                    conds_final[i] /= counts_final[i]
                del counts_final
                return conds_final
        finally:
            for callback in comfy.patcher_extension.get_all_callbacks(IndexListCallbacks.EXECUTE_CLEANUP, self.callbacks):
                callback(self, model, x_in, conds, timestep, model_options)