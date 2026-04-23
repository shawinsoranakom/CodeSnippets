def do_cross_ref(self, device, dtype, op, *, run_all):
        test_keys = [
            (torch.device(device).type, dtype, op.name),
            (None, dtype, op.name),
            (None, None, op.name),
        ]
        if any(key in CROSS_REF_EXCLUDE_SET for key in test_keys):
            self.skipTest(f"{op.name} in {dtype} not supported")

        skip_decomp_vjp = any(
            key in CROSS_REF_BACKWARD_EXCLUDE_SET for key in test_keys
        )

        requires_grad = (
            op.supports_autograd
            and dtype in op.supported_backward_dtypes(torch.device(device).type)
            # TODO: OpInfo really ought to error out for this case, but it's
            # not exercised in test_ops_gradients atm.  The problem is not
            # complex32 per-se (which is supported by data movement only ops)
            # but that when we do backwards we expect other ops like add to work
            and dtype != torch.complex32
        )
        samples = op.sample_inputs(device, dtype, requires_grad=requires_grad)

        aten_name = op.decomp_aten_name or op.aten_name

        func = op.get_op()

        def run_without_python_dispatcher(mode):
            return any(
                isinstance(op, torch._ops.OpOverload)
                and op.has_kernel_for_dispatch_key(
                    DispatchKey.CompositeImplicitAutograd
                )
                for op in mode.decomposed.union([func])
            )

        for sample_input in samples:
            if requires_grad:
                fn, primals = normalize_op_input_output(func, sample_input)
                primals = tree_map(
                    lambda x: x if isinstance(x, torch.Tensor) else x, primals
                )

                # Once https://github.com/pytorch/pytorch/pull/75965/ I can
                # store the called list on the mode object instance and no
                # explicit clearing is necessary as I will create a fresh mode
                # for each region
                with (
                    self.DecompCrossRefMode(
                        self, self.precision, self.rel_tol, dtype, run_all
                    ) as mode,
                    enable_python_dispatcher(),
                ):
                    decomp_out, decomp_vjp_fn = ref_vjp_no_create(fn, *primals)
                if run_without_python_dispatcher(mode):
                    # without this check, incorrect decomps at the python dispatcher level can still pass because
                    # they're checking aten decomps at the torch_dispatch level.
                    with self.DecompCrossRefMode(
                        self, self.precision, self.rel_tol, dtype, run_all
                    ) as mode:
                        decomp_out, decomp_vjp_fn = ref_vjp_no_create(fn, *primals)
                if aten_name in decomposition_names:
                    self.check_decomposed(aten_name, mode)

                if not skip_decomp_vjp and (
                    op.aten_backward_name in decomposition_names or run_all
                ):
                    cotangents = tree_map(lambda x: torch.randn_like(x), decomp_out)

                    with (
                        self.DecompCrossRefMode(
                            self, self.precision, self.rel_tol, dtype, run_all
                        ) as mode,
                        enable_python_dispatcher(),
                    ):
                        decomp_vjp_fn(cotangents)
                    if run_without_python_dispatcher(mode):
                        # without this check, incorrect decomps at the python dispatcher level can still pass because
                        # they're checking aten decomps at the torch_dispatch level.
                        with self.DecompCrossRefMode(
                            self, self.precision, self.rel_tol, dtype, run_all
                        ) as mode:
                            decomp_vjp_fn(cotangents)
                    if not run_all:
                        self.check_decomposed(op.aten_backward_name, mode)

            elif aten_name in decomposition_names or run_all:
                args = [sample_input.input] + list(sample_input.args)
                kwargs = sample_input.kwargs
                # A failure here might be because the decomposition for the op is wrong or because a
                # decomposition used by the particular op is wrong.
                with (
                    self.DecompCrossRefMode(
                        self, self.precision, self.rel_tol, dtype, run_all
                    ) as mode,
                    enable_python_dispatcher(),
                ):
                    func(*args, **kwargs)

                if run_without_python_dispatcher(mode):
                    # without this check, incorrect decomps at the python dispatcher level can still pass because
                    # they're checking aten decomps at the torch_dispatch level.
                    with self.DecompCrossRefMode(
                        self, self.precision, self.rel_tol, dtype, run_all
                    ) as mode:
                        func(*args, **kwargs)

                if not run_all:
                    self.check_decomposed(aten_name, mode)
            else:
                if not op.supports_autograd:
                    raise AssertionError("expected op.supports_autograd")
                self.skipTest(
                    "only backwards is decomposed, but dtype doesn't support AD"
                )