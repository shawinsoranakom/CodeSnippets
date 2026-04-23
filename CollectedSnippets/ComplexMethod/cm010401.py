def call_triton_kernel(
        self,
        variable: Union["TritonKernelVariable", "TraceableTritonKernelWrapper"],
        args: Sequence[Any],
        kwargs: dict[str, Any],
        tx: Optional["InstructionTranslator"],
    ) -> Optional["ConstantVariable"]:
        from triton import JITFunction
        from triton.runtime.autotuner import autotune, Autotuner, Config, Heuristics

        # Check if num_ctas is in kwargs
        if "num_ctas" in kwargs:
            self.raise_unsupported(
                "Passing num_ctas directly to the Triton kernel is not supported. "
                "Please use a Config in @triton.autotune instead."
            )

        # Make sure the kernel has a grid
        if variable.grid is None:
            self.raise_unsupported("Triton kernels should always be called with a grid")

        # raise an exception if there are multiple @triton.autotune decorators
        iter_kernel = variable.kernel
        autotuner_count = 0
        while not isinstance(iter_kernel, JITFunction):
            if isinstance(iter_kernel, Autotuner):
                autotuner_count += 1
            if autotuner_count > 1:
                self.raise_unsupported(
                    "Passing multiple @triton.autotune decorators is not supported. "
                    "Please use a single @triton.autotune decorator instead."
                )

            iter_kernel = iter_kernel.fn

        # Process the @triton.heuristics decorator:
        # - We know there is only 1 autotuner decorator here
        # - We can apply the heuristic to all triton.Configs in the order that the decorators appear
        #   This way, when the config is selected, the heuristics have already been applied.
        # - Decorators that appear *before* the autotuner are already processed correctly
        if isinstance(variable.kernel, Autotuner) and isinstance(
            variable.kernel.fn, Heuristics
        ):
            # unwrap the heuristics decorator, we don't need it anymore
            # variable.kernel ==> Autotuner
            # variable.kernel.fn ==> Heuristics
            # ...
            # There can be arbitrarily many heuristics wrappers here!
            # ...
            # variable.kernel.fn ==> JITFunction

            # Copy the configs, we are going to be modifying them
            new_configs = copy.deepcopy(variable.kernel.configs)

            named_args = dict(zip(variable.kernel.arg_names, args))

            # Iterate through all of the heuristics wrappers that come after the autotune wrapper
            iter_kernel = variable.kernel.fn
            while isinstance(iter_kernel, Heuristics):
                # For each config, apply the heuristic fn(s)
                for config_idx in range(len(new_configs)):
                    for kwarg_key, heuristic_fn in iter_kernel.values.items():
                        # Run heuristics on the combined configs + kwargs
                        heuristic_result = self.call_user_defined_fn(
                            heuristic_fn,
                            [
                                {
                                    **named_args,
                                    **kwargs,
                                    **new_configs[config_idx].__dict__["kwargs"],
                                },
                            ],
                            {},
                            tx,
                            variable,
                        )

                        # Update the kwargs in each config
                        # maybe_unpack_heuristic_result raises unsupported if the value is non-constant
                        new_configs[config_idx].__dict__["kwargs"][kwarg_key] = (
                            self.maybe_unpack_heuristic_result(heuristic_result)
                        )

                iter_kernel = iter_kernel.fn
            if not isinstance(iter_kernel, JITFunction):
                raise AssertionError(
                    f"Expected iter_kernel to be a JITFunction, got {type(iter_kernel)}"
                )
            prune_configs_by = {
                "perf_model": variable.kernel.perf_model,
                "early_config_prune": variable.kernel.early_config_prune,
                "configs_top_k": variable.kernel.configs_top_k,
            }
            new_kernel = autotune(
                configs=new_configs, key=[], prune_configs_by=prune_configs_by
            )(iter_kernel)
            # create a new variable to contain the new (wrapped) kernel;
            # skip kernel_idx to get a new record in the kernel side table
            new_var = self.recreate_variable(
                variable,
                kernel=new_kernel,
                kernel_idx=None,
                grid=variable.grid,
            )
            return self.call_triton_kernel(new_var, args, kwargs, tx)

        SPECIAL_CONFIG_NAMES = {
            "num_warps",
            "num_stages",
            "num_ctas",
            "num_consumer_groups",
            "num_buffers_warp_spec",
            "num_cpu_threads",
        }

        # move special config names to configs out of kwargs
        special_kwargs = {}
        for name in SPECIAL_CONFIG_NAMES:
            if name in kwargs:
                # remove special kwargs from `kwargs`
                val = kwargs.pop(name)
                special_kwargs[name] = self.get_value(val)

        if special_kwargs:
            if isinstance(variable.kernel, Autotuner):
                # if there is Autotuner already, set
                # special kwargs to each of its configs
                new_configs = copy.deepcopy(variable.kernel.configs)
                for config in new_configs:
                    config.__dict__.update(special_kwargs)
                prune_configs_by = {
                    "perf_model": variable.kernel.perf_model,
                    "early_config_prune": variable.kernel.early_config_prune,
                    "configs_top_k": variable.kernel.configs_top_k,
                }

                new_kernel = autotune(
                    configs=new_configs, key=[], prune_configs_by=prune_configs_by
                )(variable.kernel.fn)
            else:
                # if there is no Autotuner, wrap the kernel into a
                # new one with a single config with special kwargs
                new_config = Config(kwargs={}, **special_kwargs)

                new_kernel = autotune(configs=[new_config], key=[])(variable.kernel)

            # create a new variable to contain the new (wrapped) kernel;
            # skip kernel_idx to get a new record in the kernel side table
            new_var = self.recreate_variable(
                variable,
                kernel=new_kernel,
                kernel_idx=None,
                grid=variable.grid,
            )
            return self.call_triton_kernel(new_var, args, kwargs, tx)

        if isinstance(variable.kernel, Autotuner):
            special_param_names = []
            for name in SPECIAL_CONFIG_NAMES:
                if name in variable.kernel.fn.arg_names:
                    special_param_names.append(name)

            if special_param_names:
                # If the Triton kernel has SPECIAL_CONFIG_NAMES in parameters, those should
                # be passed from the kernel configs: the behavior of Triton runtime is that
                # those values get folded into the kernel arguments iff there are parameters
                # with the same name. Normally the values of those parameters are defined
                # outside the `kwargs` part of the autotuning configs. Here we move them to
                # the `kwargs` part (if they're absent there) to facilitate passing them as
                # arguments to the kernel downstream.
                updated = False
                new_configs = copy.deepcopy(variable.kernel.configs)
                for config in new_configs:
                    for name in special_param_names:
                        if name not in config.__dict__["kwargs"]:
                            if name not in config.__dict__:
                                raise AssertionError(
                                    f"{name} must be in autotuning configs to be used "
                                    "as a kernel parameter"
                                )
                            config.__dict__["kwargs"][name] = config.__dict__[name]
                            updated = True

                if updated:
                    prune_configs_by = {
                        "perf_model": variable.kernel.perf_model,
                        "early_config_prune": variable.kernel.early_config_prune,
                        "configs_top_k": variable.kernel.configs_top_k,
                    }

                    new_kernel = autotune(
                        configs=new_configs, prune_configs_by=prune_configs_by, key=[]
                    )(variable.kernel.fn)
                    new_var = self.recreate_variable(
                        variable,
                        kernel=new_kernel,
                        kernel_idx=None,
                        grid=variable.grid,
                    )
                    return self.call_triton_kernel(new_var, args, kwargs, tx)

        # These are the default values in upstream Triton
        # see: https://github.com/triton-lang/triton/blob/e57b46897191b3b3061c78d0d60e58e94be565b6/python/triton/runtime/autotuner.py
        default_perf_model = None
        default_early_config_prune = None

        # run prune_configs_by
        if isinstance(variable.kernel, Autotuner) and (
            variable.kernel.perf_model != default_perf_model
            or variable.kernel.early_config_prune != default_early_config_prune
        ):
            # Prune the configs
            named_args = dict(zip(variable.kernel.arg_names, args))

            # The source information is important here so the guards are installed correctly

            wrapped_early_configs_prune = self.wrap_user_defined_obj(
                variable.kernel.early_config_prune,
                tx,
                variable,
                "early_config_prune",
            )

            wrapped_perf_model = self.wrap_user_defined_obj(
                variable.kernel.perf_model, tx, variable, "perf_model"
            )

            wrapped_configs_top_k = self.wrap_user_defined_obj(
                variable.kernel.configs_top_k, tx, variable, "configs_top_k"
            )

            wrapped_configs = self.wrap_user_defined_obj(
                variable.kernel.configs, tx, variable, "configs"
            )

            pruned_configs = self.call_user_defined_fn(
                self.do_prune_configs,
                [
                    variable,
                    wrapped_early_configs_prune,
                    wrapped_perf_model,
                    wrapped_configs_top_k,
                    wrapped_configs,
                    named_args,
                    kwargs,
                ],
                {},
                tx,
                variable,
            )

            pruned_configs = self.maybe_unpack_configs(pruned_configs, tx)

            # after pruning the configs, create a new autotuner object with
            # these configs and recurse.
            new_kernel = autotune(configs=pruned_configs, key=[])(variable.kernel.fn)
            # create a new variable to contain the new (wrapped) kernel;
            # skip kernel_idx to get a new record in the kernel side table
            new_var = self.recreate_variable(
                variable,
                kernel=new_kernel,
                kernel_idx=None,
                grid=variable.grid,
            )
            return self.call_triton_kernel(new_var, args, kwargs, tx)

        # Both for grid's meta as well as for the kernel, we need combined
        # args and kwargs combined and normalized

        combined_args_raw = {**dict(zip(variable.kernel.arg_names, args)), **kwargs}

        # precompute the grid for the kernel
        configs = (
            [config.kwargs for config in variable.kernel.configs]
            if isinstance(variable.kernel, Autotuner)
            else [{}]
        )
        grids = []
        for config_args in configs:
            # If the grid is a function, then lets execute it and convert it to
            # a list
            grid = variable.grid
            if grid is None:
                raise AssertionError("grid cannot be None at this point")
            if self.is_callable(grid):
                # Populate the special "meta" argument to call the grid function
                meta = {**combined_args_raw, **config_args}
                grid = self.call_grid(grid, meta, tx)  # type: ignore[arg-type]
            grids.append(self.check_grid(grid))

        for i in range(len(grids)):
            if not isinstance(grids[i], tuple):
                self.raise_unsupported("Only tuple grids are supported")
            # inductor expects all grids to be 3-tuple so lets make it
            if len(grids[i]) == 1:
                grids[i] = (grids[i][0], 1, 1)
            elif len(grids[i]) == 2:
                grids[i] = (grids[i][0], grids[i][1], 1)
            elif len(grids[i]) > 3:
                self.raise_unsupported("Grid can have at most rank 3")

        if len(grids) == 0:
            raise AssertionError("grids cannot be empty")
        if isinstance(variable.kernel, JITFunction):
            constexprs = [p.num for p in variable.kernel.params if p.is_constexpr]
            arg_names = [p.name for p in variable.kernel.params]
        else:
            # If we are looking at an @triton.autotune decorator, the nested function should be a JITFunction
            # This is because we don't support @triton.heuristics or nested @triton.autotune decorators yet
            if not isinstance(variable.kernel, Autotuner):
                raise AssertionError(
                    f"Expected variable.kernel to be an Autotuner, got {type(variable.kernel)}"
                )
            constexprs = [p.num for p in variable.kernel.fn.params if p.is_constexpr]
            arg_names = [p.name for p in variable.kernel.fn.params]

        for idx, arg_name in enumerate(arg_names):
            if idx in constexprs:
                if arg_name in combined_args_raw:
                    # [Note: Specialize tl.constexpr args in user-defined triton kernels]
                    # This arg is marked as tl.constexpr. That means that triton will recompile every time
                    # this value changes.
                    # https://github.com/pytorch/pytorch/issues/136504
                    # One option is to correctly pass the symints in so that the symbolic expressions are defined
                    # when the triton code is being executed.
                    # But since triton will have to recompile either way, we instead just specialize on the value.
                    #
                    # Depending on the type of `variable` we might expect different types for the symbolic args:
                    # either SymNodeVariables (for TritonKernelVariables) or SymInts (TracingTritonKernelWrapper)
                    combined_args_raw[arg_name] = variable.specialize_symbolic(
                        combined_args_raw[arg_name]
                    )
        return self.call_HOP(variable, grids, combined_args_raw, tx)