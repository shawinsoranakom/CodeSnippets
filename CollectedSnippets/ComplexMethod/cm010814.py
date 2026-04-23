def convert(idx: int, x: Any) -> Any:
            nonlocal ignore_shape_env
            if shape_env is not None and not ignore_shape_env:
                from torch._dynamo.source import ConstantSource

                if isinstance(x, int):
                    # We always specialize on scalar values in export.
                    if aot_config.is_export:
                        return x
                    source = ConstantSource(f"sym_{idx}")
                    return shape_env.create_symintnode(
                        shape_env.create_symbol(x, source, positive=x >= 0),
                        hint=x,
                        source=source,
                    )
            if isinstance(x, torch.ScriptObject) or is_opaque_type(type(x)):
                return torch._library.fake_class_registry.maybe_to_fake_obj(
                    fake_mode, x
                )
            if not isinstance(x, torch.Tensor):
                return x
            if isinstance(x, FakeTensor):
                # In the case of cross compilation we will have example inputs
                # with a different fake mode than our tracing fake mode.
                # In these cases we want to clone the fake tensor into our
                # inner fake mode.
                if x.fake_mode is not fake_mode:
                    return fake_mode.from_tensor(x)
                return x
            if is_traceable_wrapper_subclass(x):
                attrs, _ = x.__tensor_flatten__()
                # See if all inner tensors are FakeTensors from this mode
                all_this_fake = True
                for a in attrs:
                    match getattr(x, a):
                        case FakeTensor() as v:
                            if v.fake_mode is not fake_mode:
                                # FakeTensor subclass from a different mode.
                                # Fall through to refakify.
                                all_this_fake = False
                                break
                        case torch.Tensor():
                            all_this_fake = False
                            break
                        case OpaqueBase():
                            pass
                        case unexpected:
                            raise AssertionError(
                                f"expected Tensor or OpaqueBase, got {type(unexpected)}"
                            )

                if all_this_fake:
                    return x

            # see note [Tensor Fakification and Symbol Caching]
            symbolic_context = None
            source = None
            trace = True
            if tracing_context := torch._guards.TracingContext.try_get():
                if x in tracing_context.tensor_to_context:
                    symbolic_context = tracing_context.tensor_to_context[x]
                    source = symbolic_context.tensor_source
                    # We already fakeified this tensor in Dynamo, don't
                    # dump the trace for it again
                    trace = False
            if (
                idx < aot_config.num_params_buffers
                and config.static_weight_shapes
                and not symbolic_context
            ):
                # TODO: Ensure that this codepath is never exercised from
                # Dynamo
                return fake_mode.from_tensor(x, static_shapes=True)

            result = fake_mode.from_tensor(
                x,
                static_shapes=ignore_shape_env,
                symbolic_context=symbolic_context,
                source=source,
                trace=trace,
            )
            return result