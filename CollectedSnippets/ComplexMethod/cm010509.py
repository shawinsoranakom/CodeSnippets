def __call__(
        self,
        t: torch.Tensor,
        shape_env: ShapeEnv | None = None,
        *,
        callback: _MetaTensorCallback[_TensorT] | None = None,
        source: Source | None = None,
        symbolic_context: SymbolicContext | None = None,
        # Controls whether or not we should dump the tensor metadata to structured logs
        # when source is not None.  Because we refakify after Dynamo is done,
        # we don't want to dump info again from AOTAutograd, it is redundant.
        trace: bool = True,
    ) -> _TensorT:
        callback_: _MetaTensorCallback[_TensorT]
        if callback is None:
            callback_ = self._identity_callable
        else:
            callback_ = callback
        # TODO: zero tensors?  We appear to have eliminated them by
        # excluding complex for now

        # Filter out cases we don't support
        # TODO: This can probably be simplified quite a bit
        if isinstance(t, torch.Tensor):
            if (
                # Lazy tensors are not supported.  Note that XLA is
                # implemented on top of lazy tensor, not excluded here; we
                # have some special handling for it; this is for XLA Dynamo
                # integration
                t.device.type == "lazy"
                or
                # Quantization is not supported
                t.is_quantized
                or
                # Views out of sparse tensors not currently supported (plain
                # sparse is supported htough)
                (t._is_view() and t._base is not None and t._base.is_sparse)
            ):
                self.miss += 1
                # pyrefly: ignore [bad-return]
                return NotImplemented
            else:
                self.hit += 1
        elif torch.overrides.is_tensor_like(t):
            self.miss += 1
            # pyrefly: ignore [bad-return]
            return NotImplemented
        else:
            # non-Tensor types don't count as hit or miss
            return t

        if source is None:
            trace = False

        # Describe the tensor.  NB: do NOT disable ambient modes, we may need
        # to query them when figuring out what to put in here
        t_desc = self.describer.describe_tensor(t, trace=trace)

        if trace:
            if source is None:
                raise AssertionError("source must not be None when trace is True")
            trace_structured(
                "describe_source",
                metadata_fn=lambda: {
                    "describer_id": self.describer.id,
                    "id": t_desc.id,
                    "source": source.name,
                },
            )

        # Do the meta-fication.  Here, we disable all the ambient modes, to
        # better simulate what would be like to re-fakeify from a fresh
        # process
        with contextlib.ExitStack() as exit_stack:
            exit_stack.enter_context(torch._dispatch.python.suspend_functionalization())
            st = peek_interpreter_stack()
            if st is not None:
                exit_stack.enter_context(
                    torch._functorch.pyfunctorch.temporarily_clear_interpreter_stack()
                )

            r = self.meta_tensor(
                t_desc,
                shape_env,
                callback_,
                source,
                symbolic_context,
            )

        if type(t) is torch.nn.Parameter:
            # NB: Cannot directly use Parameter constructor
            # because that would force a detach, not desirable
            r._is_param = True

        # forward the 'is_buffer' metadata if present (for nn.Buffer checks)
        if getattr(t, "_is_buffer", False):
            # pyrefly: ignore [missing-attribute]
            r._is_buffer = True
            if hasattr(t, "persistent"):
                # pyrefly: ignore [missing-attribute]
                r.persistent = t.persistent

        # TODO: return the description for later
        return r