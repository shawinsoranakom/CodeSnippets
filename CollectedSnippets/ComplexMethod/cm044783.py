def _get_clipping_scale(self, group: dict, tuples: List[Tuple[Tensor, dict, List[str]]]) -> float:
        """
        Returns a scalar factor <= 1.0 that dictates gradient clipping, i.e. we will scale the gradients
        by this amount before applying the rest of the update.

        Args:
           group: the parameter group, an item in self.param_groups
           tuples: a list of tuples of (param, state, param_names)
                where param is a batched set of parameters,
                with a .grad (1st dim is batch dim)
                and state is the state-dict where optimization parameters are kept.
                param_names is a List[str] while each str is name for a parameter
                in batched set of parameters "param".
        """
        assert len(tuples) >= 1
        clipping_scale = group["clipping_scale"]
        (first_p, first_state, _) = tuples[0]
        step = first_state["step"]
        if clipping_scale is None or step == 0:
            # no clipping.  return early on step == 0 because the other
            # parameters' state won't have been initialized yet.
            return 1.0
        clipping_update_period = group["clipping_update_period"]

        tot_sumsq = torch.tensor(0.0, device=first_p.device)
        for p, state, param_names in tuples:
            grad = p.grad
            if grad.is_sparse:
                raise RuntimeError("ScaledAdam optimizer does not support sparse gradients")
            if p.numel() == p.shape[0]:  # a batch of scalars
                tot_sumsq += (grad**2).sum()  # sum() to change shape [1] to []
            else:
                tot_sumsq += ((grad * state["param_rms"]) ** 2).sum()

        tot_norm = tot_sumsq.sqrt()
        if "model_norms" not in first_state:
            first_state["model_norms"] = torch.zeros(clipping_update_period, device=p.device)
        first_state["model_norms"][step % clipping_update_period] = tot_norm

        if step % clipping_update_period == 0:
            # Print some stats.
            # We don't reach here if step == 0 because we would have returned
            # above.
            sorted_norms = first_state["model_norms"].sort()[0].to("cpu")
            quartiles = []
            for n in range(0, 5):
                index = min(
                    clipping_update_period - 1,
                    (clipping_update_period // 4) * n,
                )
                quartiles.append(sorted_norms[index].item())

            median = quartiles[2]
            threshold = clipping_scale * median
            first_state["model_norm_threshold"] = threshold
            percent_clipped = (
                first_state["num_clipped"] * 100.0 / clipping_update_period if "num_clipped" in first_state else 0.0
            )
            first_state["num_clipped"] = 0
            quartiles = " ".join(["%.3e" % x for x in quartiles])
            logging.info(
                f"Clipping_scale={clipping_scale}, grad-norm quartiles {quartiles}, threshold={threshold:.3e}, percent-clipped={percent_clipped:.1f}"
            )

        if step < clipping_update_period:
            return 1.0  # We have not yet estimated a norm to clip to.
        else:
            try:
                model_norm_threshold = first_state["model_norm_threshold"]
            except KeyError:
                logging.info(
                    "Warning: model_norm_threshold not in state: possibly you changed config when restarting, adding clipping_scale option?"
                )
                return 1.0
            ans = min(1.0, (model_norm_threshold / (tot_norm + 1.0e-20)).item())
            if ans < 1.0:
                first_state["num_clipped"] += 1
            if ans < 0.1:
                logging.warning(f"Scaling gradients by {ans}, model_norm_threshold={model_norm_threshold}")
                if self.show_dominant_parameters:
                    assert p.shape[0] == len(param_names)
                    self._show_gradient_dominating_parameter(tuples, tot_sumsq)
            return ans