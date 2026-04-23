def from_real_tensor(
        self,
        fake_mode: FakeTensorMode,
        t: Tensor,
        make_constant: bool = False,
        shape_env: ShapeEnv | None = None,
        *,
        source: Source | None = None,
        symbolic_context: SymbolicContext | None = None,
        trace: bool = True,
    ) -> FakeTensor:
        # see note [Tensor Fakification and Symbol Caching]
        if not symbolic_context and not source and shape_env:
            if tracing_context := torch._guards.TracingContext.try_get():
                if t in tracing_context.tensor_to_context:
                    symbolic_context = tracing_context.tensor_to_context[t]
                    from torch.fx.experimental.symbolic_shapes import (
                        StatefulSymbolicContext,
                    )

                    if not isinstance(symbolic_context, StatefulSymbolicContext):
                        raise AssertionError(
                            f"Expected StatefulSymbolicContext, got {type(symbolic_context)}"
                        )
                    source = symbolic_context.tensor_source

        maybe_memo = self._get_memo(t)
        if maybe_memo is not None:
            return maybe_memo
        # not yet supported in metatensors
        if t.is_quantized:
            raise UnsupportedFakeTensorException("quantized nyi in meta tensors")
        if type(t) is torch.nn.Parameter:
            if make_constant:
                raise AssertionError("make_constant must be False for nn.Parameter")

        constant = t if make_constant else None

        # This callback is used by both subclass and inner tensors. Require the
        # caller to explicitly specify the device in case outer and inner tensors
        # have different devices.
        def mk_fake_tensor(
            make_meta_t: Callable[[], object], device: torch.device | str
        ) -> FakeTensor:
            # NB: don't use in_kernel_invocation_manager. to
            # ensure FakeTensor can internally do constant computation
            # as necessary.  Invocation manager is "more correct" as
            # it works for more operators in make_meta_t, but
            # invariant is that make_meta_t only calls factories
            # for which it is not strictly necessary to use the
            # invocation manager (I think!)
            with no_dispatch():
                return FakeTensor(
                    fake_mode,
                    # pyrefly: ignore [bad-argument-type]
                    make_meta_t(),
                    # pyrefly: ignore [bad-argument-type]
                    device,
                    # TODO: callback might be used in recursive contexts, in
                    # which case using t is wrong!  BUG!
                    constant=constant,
                )

        out = self.meta_converter(
            t,
            shape_env=shape_env,
            callback=mk_fake_tensor,
            source=source,
            symbolic_context=symbolic_context,
            trace=trace,
        )
        if out is NotImplemented:
            raise UnsupportedFakeTensorException("meta converter nyi")

        # Propagate grad_dtype here rather than in meta_converter because
        # meta tensors don't carry autograd metadata.
        # Unwrap FunctionalTensor because accessing is_leaf/grad_fn on a
        # FunctionalTensor view whose base was mutated (e.g. via set_())
        # triggers lazy view replay through __torch_dispatch__, which
        # errors without an active FunctionalTensorMode.
        inner_t = (
            torch._from_functional_tensor(t.elem)
            if isinstance(t, torch._subclasses.functional_tensor.FunctionalTensor)
            else t
        )
        if (
            inner_t.requires_grad
            and inner_t.is_leaf
            and inner_t.grad_dtype != inner_t.dtype
            and out.is_leaf
        ):
            out.grad_dtype = inner_t.grad_dtype

        from torch._dynamo.source import RandomValueSource

        value = None
        if (
            not self.export
            and _is_plain_tensor(t)  # mostly, we want to know if item() works
            and t.dim() == 0
            and t.device.type == "cpu"
            # All integer types are fair game, because signed overflow is UB
            # (and even int64 can overflow, since integers in Python are
            # arbitrary precision). But only float64 is OK for float, because
            # switching between float32 and float64 changes semantics in an
            # observable way without hitting UB.
            and t.dtype
            in [torch.int64, torch.int32, torch.int16, torch.int8, torch.float64]
            and source is not None
            # Impede setting up item() on things coming from random.  These
            # are not "real" item() calls, instead UnspecializedPythonVariable
            # is unsafely pretending an int is a tensor, which can sometimes
            # implicitly cause an item call.  The problem is this is pretty
            # unsound: there's no reason substituting an int with a Tensor is
            # going to give the same results.  Today, you mostly get around
            # this by typically not having capture_scalar_outputs on and graph
            # breaking when someone tries to use the unspec variable in an
            # int-y context.  But allowing it through here would break that.
            # So don't.
            #
            # Once random values are setup to be represented as
            # SymNodeVariable, this condition can be removed.  To check if
            # you've done it right, this is a good test:
            #
            #   PYTORCH_TEST_WITH_DYNAMO=1 python test/test_reductions.py -k
            #   TestReductionsCPU.test_dim_reduction_fns_fn_name_amax_cpu_bfloat16
            and not isinstance(source, RandomValueSource)
            # In Dynamo, shape_env is never none (even with static shapes).
            # However, FakeTensorMode can be used by hand and in some cases
            # ShapeEnv is not allocated.
            and shape_env is not None
        ):
            from torch._dynamo.source import CallMethodItemSource, FloatTensorSource
            from torch.fx.experimental.symbolic_shapes import DimDynamic

            with no_dispatch():
                value = t.item()
            if not math.isnan(value) and not math.isinf(value):
                # Peephole strip out unnecessary torch.as_tensor(x).item()
                if isinstance(source, FloatTensorSource):
                    item_source = source.base
                else:
                    item_source = CallMethodItemSource(source)
                symbol = shape_env.create_unspecified_symbol(
                    value,
                    source=item_source,
                    dynamic_dim=DimDynamic.DYNAMIC,
                    symbolic_context=symbolic_context,
                )
                # NB: reusing item_memo here ensures that we invalidate on
                # mutation
                if t.dtype == torch.int64:
                    out.item_memo = shape_env.create_symintnode(
                        symbol,
                        hint=value,
                        source=item_source,
                    )
                elif t.dtype == torch.float64:
                    out.item_memo = shape_env.create_symfloatnode(
                        symbol,
                        hint=value,
                        source=item_source,
                    )
        if make_constant:
            self.add_constant_storage_mapping(out)
        # NB: meta_converter set the memo
        return out