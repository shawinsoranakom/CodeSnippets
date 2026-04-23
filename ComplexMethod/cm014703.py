def test_rosenbrock_sparse(self, device, dtype, optim_info, with_lrsched):
        optim_cls = optim_info.optim_cls

        # Skip differentiable testing for now, see https://github.com/pytorch/pytorch/issues/116490
        # Fused impls do not support sparse gradients
        all_optim_inputs = _get_optim_inputs_including_global_cliquey_kwargs(
            device, dtype, optim_info, skip=("differentiable", "fused")
        )
        kwarg_updates, schedulers_constructors = optim_info.metadata_for_sparse

        if with_lrsched and len(schedulers_constructors) == 0:
            return

        supported_inputs = []
        if len(kwarg_updates) != 0:
            seen = set()
            for i in all_optim_inputs:
                for k in kwarg_updates:
                    if k in i.kwargs:
                        del i.kwargs[k]
                hashable_kwargs = tuple(sorted(i.kwargs.items()))
                if len(i.kwargs) > 0 and hashable_kwargs not in seen:
                    supported_inputs.append(i)
                    seen.add(hashable_kwargs)
                    if "lr" in kwarg_updates:
                        i.kwargs["lr"] = kwarg_updates["lr"]
        else:
            supported_inputs = all_optim_inputs

        for optim_input in supported_inputs:
            kwargs = optim_input.kwargs
            multi_tensor = kwargs.get("foreach", False)

            # For rosenbrock tests, it is mandated that the param is a tensor with 2 numbers
            if multi_tensor:
                params_t = [
                    torch.tensor([1.5, 1.5]),
                    torch.tensor([1.5, 1.5], dtype=dtype),
                ]
            else:
                params_t = [torch.tensor([1.5, 1.5])]

            params = [Parameter(param_t) for param_t in params_t]
            optimizer = optim_cls(params, **kwargs)
            schedulers = [
                s(optimizer) for s in (schedulers_constructors if with_lrsched else [])
            ]

            if not optim_info.only_supports_sparse_grads:
                params_c = [Parameter(param_t.clone()) for param_t in params_t]
                optimizer_c = optim_cls(params_c, **kwargs)
                schedulers_c = [
                    s(optimizer_c)
                    for s in (schedulers_constructors if with_lrsched else [])
                ]

            solution = torch.tensor([1, 1])
            with torch.no_grad():
                initial_dist = sum(param.dist(solution) for param in params)

            def get_grad(param, sparse_grad, w):
                grad = drosenbrock(param)
                # NB: We torture test the optimizer by returning an
                # uncoalesced sparse tensor

                # Depending on w, provide only the x or y gradient
                if sparse_grad:
                    if w:
                        i = torch.tensor([[0, 0]], dtype=torch.int64)
                        x = grad[0]
                        v = torch.tensor([x / 4.0, x - x / 4.0])
                    else:
                        i = torch.tensor([[1, 1]], dtype=torch.int64)
                        y = grad[1]
                        v = torch.tensor([y - y / 4.0, y / 4.0])
                    grad_out = torch.sparse_coo_tensor(i, v, (2,), dtype=v.dtype)
                else:
                    if w:
                        grad_out = torch.tensor([grad[0], 0], dtype=param.dtype)
                    else:
                        grad_out = torch.tensor([0, grad[1]], dtype=param.dtype)
                return grad_out

            def eval(params, sparse_grad, w):
                optimizer.zero_grad()
                if multi_tensor:
                    loss = sum(rosenbrock(param) for param in params)
                else:
                    loss = rosenbrock(params[0])
                loss.backward()

                grads_out = [get_grad(param, sparse_grad, w) for param in params]
                with torch.no_grad():
                    params[0].grad = grads_out[0]
                    if multi_tensor:
                        params[1].grad = grads_out[1].to(dtype=dtype)
                return loss

            for i in range(1800):
                # Do cyclic coordinate descent
                w = i % 2
                optimizer.step(functools.partial(eval, params, True, w))
                for scheduler in schedulers:
                    if isinstance(scheduler, ReduceLROnPlateau):
                        scheduler.step(rosenbrock(params[0]))
                    else:
                        scheduler.step()
                if not optim_info.only_supports_sparse_grads:
                    optimizer_c.step(functools.partial(eval, params_c, False, w))
                    for scheduler in schedulers_c:
                        if isinstance(scheduler, ReduceLROnPlateau):
                            scheduler.step(rosenbrock(params_c[0]))
                        else:
                            scheduler.step()
                    # Tolerance is increased due to floating point error from different
                    # code path for dense case: x v.s. x - x / 4.0 + x / 4.0
                    self.assertEqual(params, params_c, atol=5e-6, rtol=5e-6)

            if not kwargs.get("maximize", False):
                self.assertLessEqual(
                    sum(param.dist(solution) for param in params), initial_dist
                )
            else:
                self.assertGreaterEqual(
                    sum(rosenbrock(param) for param in params),
                    sum(rosenbrock(param_t) for param_t in params_t),
                )