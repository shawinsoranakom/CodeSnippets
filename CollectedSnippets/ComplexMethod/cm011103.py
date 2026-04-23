def _use_unsharded_grad_views(self) -> None:
        """
        Unflatten the unsharded flat parameter's gradient.

        The original parameter variables' gradients are set to be views into
        the unsharded flat parameter's gradient.
        """
        # Expects the gradient to be in `flat_param.grad`
        if self.flat_param.grad is None:
            for param in chain(self.flat_param._params, self.flat_param._shared_params):
                param.grad = None
            return
        self._check_unsharded(self.flat_param.grad)
        views = self._get_unflat_views(self.flat_param.grad)
        for i, (view, (param_name, module, _)) in enumerate(
            zip(views, self.flat_param._param_infos)
        ):
            _p_assert(
                hasattr(module, param_name),
                f"{self.flat_param._fqns[i]} is missing",
            )
            param = getattr(module, param_name)
            if (
                param.shape != view.shape
                or param.dtype != view.dtype
                or param.device != view.device
            ):
                # NOTE: This is a hack using `.data` to side step the check
                # that parameter/gradient sizes/dtypes/devices match. From
                # calling `reshard()`, `param` has the sharded size, has the
                # full precision dtype, and if CPU offloading is enabled, is on
                # CPU. Thus, one or more of the following cases can hold when
                # in `no_sync()`, where `view` is the original parameter's
                # gradient:
                # 1. `view` can have the unsharded size.
                # 2. `view` can have the parameter low precision dtype.
                # 3. `view` can be on GPU.
                if param.grad is None:
                    param.grad = torch.empty_like(param)
                param.grad.data = view
            else:
                param.grad = view
        for (
            param_name,
            module,
            module_name,
            prim_param_name,
            prim_module,
            _,
        ) in self.flat_param._shared_param_infos:
            _p_assert(
                hasattr(module, param_name),
                f"{module_name + '.' + param_name if module_name else param_name} is missing",
            )
            param = getattr(module, param_name)
            prim_param = getattr(prim_module, prim_param_name)
            if (
                param.shape != prim_param.grad.shape
                or param.dtype != prim_param.grad.dtype
                or param.device != prim_param.grad.device
            ):
                # NOTE: This is the same hack to use `.data` to side step the
                # size check.
                if param.grad is None:
                    param.grad = torch.empty_like(param)
                param.grad.data = prim_param.grad
            else:
                param.grad = prim_param.grad