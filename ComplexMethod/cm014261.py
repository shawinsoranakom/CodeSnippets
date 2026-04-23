def run_node(self, n: Node) -> Any:
        args, kwargs = self.fetch_args_kwargs_from_env(n)
        new_args = []
        assert self.fake_mode
        for arg in args:
            if isinstance(arg, torch.Tensor) and not isinstance(
                arg, torch._subclasses.FakeTensor
            ):
                new_args.append(torch._dynamo.utils.to_fake_tensor(arg, self.fake_mode))
            else:
                new_args.append(arg)

        log.debug("run_node %s, %s got args %s", n.op, n.target, args_str(args))
        assert isinstance(args, tuple)
        assert isinstance(kwargs, dict)

        if n.op == "call_module":
            real_mod = self.fetch_attr(str(n.target))
            if self.fake_mode:
                curr_submod = deepcopy_to_fake_tensor(real_mod, self.fake_mode)
            else:
                curr_submod = real_mod

            ddp_graph_log.debug("\n---%s graph---\n%s", n.target, curr_submod.graph)

            # When calling the compiler on the submod, inputs (new_args) are expected to
            # be FakeTensors already since Dynamo would have made them FakeTensors in the
            # non-DDP flow.  However, the parameters are _not_ expected to be FakeTensors,
            # since this wrapping happens during compilation

            # Note: Returning Fake Tensors on First AOT Autograd Call
            #
            # Inductor will optimize strides of outputs when it deems it profitable.
            # For instance, converting to channels last. When we split the graph here
            # into multiple inductor compilations, we need to make sure that the
            # output strides of one compilation is appropriately passed to the subsequent
            # compilations. However, the mapping from inductor output to dynamo output
            # is non-trivial due to aot_autograd's deduping, de-aliasing, mutation, re-writing,
            # subclass handling, etc. In order to replay all this logic we set a flag such that
            # the first invocation of inductor in aot_autograd will return Fake Tensors with
            # appropriate strides. Then, all of aot autograd's runtime logic is replayed.
            # This gives us the appropriately strided outputs here which will reflect runtime strides.

            class FakeifyFirstAOTInvocationGuard:
                def __init__(self) -> None:
                    self.tc = torch._guards.TracingContext.try_get()
                    assert self.tc
                    self.tc.fakify_first_call = True

                def __del__(self) -> None:
                    self.tc.fakify_first_call = False  # type: ignore[union-attr]

            # For aot_eager and other backends, tracing context is not set
            has_tracing_context = torch._guards.TracingContext.try_get() is not None
            if has_tracing_context:
                g = FakeifyFirstAOTInvocationGuard()  # noqa: F841

            from torch._dynamo.utils import counters

            init = counters["aot_autograd"]["total"]
            compiled_submod_real = self.compile_submod(real_mod, new_args, kwargs)

            # TODO - better way of doing this?
            # Only aot autograd handles fakifying first call
            invoked_aot_autograd = init != counters["aot_autograd"]["total"]

            # We update the original (outer) graph with a call into the compiled module
            # instead of the uncompiled one.
            self.module.delete_submodule(n.target)  # type: ignore[operator]
            n.target = "compiled_" + n.target  # type: ignore[operator]
            self.module.add_submodule(n.target, compiled_submod_real)  # type: ignore[operator]

            # Finally, we have to produce inputs for use compiling the next submodule,
            # and these need to be FakeTensors, so we execute the module under fake_mode
            # Because parameters are not fake we patch fake tensor mode to allow non fake inputs
            with (
                self.fake_mode,
                mock.patch.object(self.fake_mode, "allow_non_fake_inputs", True),
            ):
                if has_tracing_context and invoked_aot_autograd:
                    tracing_ctx = torch._guards.TracingContext.try_get()
                    assert tracing_ctx is not None
                    # DDPOptimizer maintains 1 dynamo graph -> N AOT graphs
                    # Dynamo only has 1 tracing context, so it needs to maintain all N AOT metadata instances
                    ddp_ctx = tracing_ctx.ddp_optimizer_ctx
                    assert ddp_ctx is not None
                    assert tracing_ctx.fw_metadata is not None
                    ddp_ctx.curr_bucket += 1
                    ddp_ctx.metadata_per_bucket.append(tracing_ctx.fw_metadata)

                    out = compiled_submod_real(*new_args, **kwargs)
                    # output should be fake or subclass
                    assert all(
                        (not isinstance(t, torch.Tensor) or type(t) is not torch.Tensor)
                        for t in (out if isinstance(out, (list, tuple)) else [out])
                    )
                    return out
                else:
                    return curr_submod(*new_args, **kwargs)
        else:
            # placeholder or output nodes don't need to get compiled, just executed
            return getattr(self, n.op)(n.target, new_args, kwargs)