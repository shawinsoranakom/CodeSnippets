def compile(
        self,
        graph: fx.GraphModule,
        example_inputs: list[Any],
        compiler_config: dict[str, Any],
        compile_range: Range,
        key: str | None = None,
    ) -> tuple[Callable[..., Any] | None, Any | None]:
        _apply_constrain_to_fx_strides_patch()
        compilation_counter.num_inductor_compiles += 1
        current_config = {}
        if compiler_config is not None:
            current_config.update(compiler_config)
        set_inductor_config(current_config, compile_range)
        set_functorch_config()

        if compile_range.is_single_size():
            dynamic_shapes = "from_example_inputs"
        else:
            dynamic_shapes = "from_graph"

        from torch._inductor import standalone_compile

        supports_aot = is_torch_equal_or_newer("2.10.0")

        if not supports_aot and envs.VLLM_USE_MEGA_AOT_ARTIFACT:
            logger.error(
                "CRITICAL: VLLM_USE_MEGA_AOT_ARTIFACT "
                "is enabled but PyTorch version does not support 'aot' "
                "parameter in standalone_compile. This requires PyTorch "
                "2.10.0+. Falling back to non-AOT mode."
            )

        compile_kwargs = {
            "dynamic_shapes": dynamic_shapes,
            "options": {
                "config_patches": current_config,
            },
        }

        if is_torch_equal_or_newer("2.13.0.dev"):
            compile_kwargs["donate_graph_module"] = True  # type: ignore[assignment]

        use_aot: bool = supports_aot and envs.VLLM_USE_MEGA_AOT_ARTIFACT
        # only add 'aot' parameter if both supported and enabled...
        # this will set bundled_autograd_cache
        # https://github.com/pytorch/pytorch/blob/9bbc5b2905c260adf41bc866a732f9c121a2828a/torch/_inductor/standalone_compile.py#L359 # noqa
        if use_aot:
            compile_kwargs["aot"] = True  # type: ignore[assignment]

        # Inductor's pre-grad passes don't do anything for vLLM.
        # The pre-grad passes get run even on cache-hit and negatively impact
        # vllm cold compile times by O(1s)
        # Fixed upstream in PyTorch 2.12:
        # https://github.com/pytorch/pytorch/issues/174502
        if is_torch_equal_or_newer("2.12.0.dev") or envs.VLLM_ENABLE_PREGRAD_PASSES:
            pregrad_ctx: Any = contextlib.nullcontext()
        else:
            pregrad_ctx = patch(
                "torch._inductor.compile_fx._recursive_pre_grad_passes",
                lambda gm, _: gm,
            )

        # When inputs are FakeTensors (from create_concrete_args),
        # standalone_compile("from_example_inputs") would normally create
        # a fresh FakeTensorMode, causing a mode mismatch assertion.
        # Patch FakeTensorMode in standalone_compile so it reuses the
        # mode already attached to our FakeTensors. This gives us both
        # ignore_shape_env=True (from "from_example_inputs") and mode
        # consistency (from reusing our mode).
        # Can remove this after the following issue gets fixed:
        # https://github.com/pytorch/pytorch/issues/176562
        from torch._subclasses.fake_tensor import FakeTensor

        input_fake_mode = None
        for x in example_inputs:
            if isinstance(x, FakeTensor):
                input_fake_mode = x.fake_mode
                break

        if input_fake_mode is not None:
            # Use patch.object on the actual module from sys.modules
            # because in Python <=3.10 the string-based patch() resolves
            # torch._inductor.standalone_compile to the wrapper function
            # (defined in __init__.py) instead of the module.
            import sys

            fake_mode_ctx: Any = patch.object(
                sys.modules["torch._inductor.standalone_compile"],
                "FakeTensorMode",
                lambda *a, **kw: input_fake_mode,
            )
        else:
            fake_mode_ctx = contextlib.nullcontext()

        with pregrad_ctx, fake_mode_ctx:
            compiled_graph = standalone_compile(graph, example_inputs, **compile_kwargs)

        if use_aot:
            from torch._inductor.standalone_compile import AOTCompiledArtifact

            assert isinstance(compiled_graph, AOTCompiledArtifact)
            assert hasattr(compiled_graph, "serialize")
            # just return the compiled graph and a key
            # since we can serialize the bytes using to_bytes
            # and reload it using the key when reading
            return compiled_graph, None

        # Save the compiled artifact to disk in the specified path
        assert key is not None
        path = os.path.join(self.cache_dir, key)

        def is_saveable_2_10(compiled_artifact):
            # can just use compiled_artifact.is_saveable in 2.11
            if compiled_artifact._artifacts is None:
                return False
            _, cache_info = compiled_artifact._artifacts
            return len(cache_info.aot_autograd_artifacts) == 1

        if is_compile_cache_enabled(compiler_config):
            if not is_saveable_2_10(compiled_graph):
                raise RuntimeError(
                    "The compiled artifact is not serializable. This usually means "
                    "that the model code has something that is not serializable "
                    "by torch.compile in it. You can fix this by either "
                    "figuring out what is not serializable and rewriting it, "
                    "filing a bug report, "
                    "or suppressing this error by "
                    "disabling vLLM's compilation cache via "
                    "VLLM_DISABLE_COMPILE_CACHE=1 "
                    "(this will greatly increase vLLM server warm start times)."
                )
            compiled_graph.save(path=path, format=self.save_format)
            compilation_counter.num_compiled_artifacts_saved += 1
        return compiled_graph, (key, path)