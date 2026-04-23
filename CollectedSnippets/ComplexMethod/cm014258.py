def __call__(
        self, gm: torch.fx.GraphModule, example_inputs: Sequence[Any], **kwargs: Any
    ) -> Callable[..., Any]:
        if kwargs:
            log.warning("aot_autograd-based backend ignoring extra kwargs %s", kwargs)

        if any(isinstance(x, (list, tuple, dict)) for x in example_inputs):
            return flatten_graph_inputs(
                gm,
                example_inputs,
                self,
            )

        # Hack to get around circular import problems with aot_eager_decomp_partition
        if callable(self.kwargs.get("decompositions")):
            self.kwargs["decompositions"] = self.kwargs["decompositions"]()

        # NB: dont delete counter increment
        counters["aot_autograd"]["total"] += 1
        use_fallback = False

        if use_fallback:
            log.debug("Unable to use AOT Autograd because graph has mutation")
            counters["aot_autograd"]["not_ok"] += 1
            return gm

        def wrap_bw_compiler(bw_compiler_fn: Callable[P, R]) -> Callable[..., R]:
            def _wrapped_bw_compiler(*args: P.args, **kwargs: P.kwargs) -> R:
                # Note [Wrapping bw_compiler in disable]
                # The two disables here:
                # - stop TorchDynamo from trying to compile the bw_compiler function itself
                # - stop TorchDynamo from trying to compile our the generated backwards pass bw_compiler produces

                return disable(
                    disable(
                        bw_compiler_fn, reason="do not trace backward compiler function"
                    )(*args, **kwargs),  # type: ignore[misc]
                    reason="do not trace generated backwards pass",
                )

            _wrapped_bw_compiler._is_wrapped_bw_compiler = (  # pyrefly: ignore [missing-attribute]
                True
            )
            return _wrapped_bw_compiler

        bw_compiler = self.kwargs.get("bw_compiler") or self.kwargs["fw_compiler"]

        if isinstance(bw_compiler, SerializableAOTDispatchCompiler):
            bw_compiler.compiler_fn = wrap_bw_compiler(bw_compiler.compiler_fn)
        elif getattr(bw_compiler, "_is_wrapped_bw_compiler", False):
            bw_compiler.compiler_fn = bw_compiler
        else:
            bw_compiler = wrap_bw_compiler(bw_compiler)

        self.kwargs["bw_compiler"] = bw_compiler
        self.kwargs["inference_compiler"] = (
            self.kwargs.get("inference_compiler") or self.kwargs["fw_compiler"]
        )

        from functorch.compile import nop
        from torch._inductor.debug import enable_aot_logging

        # debug asserts slow down compile time noticeably,
        # So only default them on when the aot_eager backend is used.
        if self.kwargs.get("fw_compiler", None) is nop:
            patch_config: contextlib.AbstractContextManager[Any] = patch(
                "functorch.compile.config.debug_assert", True
            )
        else:
            patch_config = contextlib.nullcontext()

        try:
            # NB: NOT cloned!
            with enable_aot_logging(), patch_config:
                cg = aot_module_simplified(gm, example_inputs, **self.kwargs)
                counters["aot_autograd"]["ok"] += 1
                return disable(cg, reason="do not trace AOT-compiled graph")
        except TensorifyScalarRestartAnalysis:
            raise
        except Exception:
            counters["aot_autograd"]["not_ok"] += 1
            raise