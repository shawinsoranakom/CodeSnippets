def inner_wrap_fake(x: object) -> object:
            nonlocal arg_count
            # TODO: it would be nice to line these up with the names
            # FX will choose for the placeholders, but we don't
            # actually know what the names will be at this point yet
            # NB: the Source here is actually meaningless
            from torch._dynamo.source import ConstantSource

            if self.fake_tensor_mode is None:
                raise AssertionError("fake_tensor_mode should not be None")
            source = ConstantSource(f"input{arg_count}")
            if isinstance(x, Tensor):
                arg_count += 1
                return self.fake_tensor_mode.from_tensor(x, source=source)
            # NB: don't match on bools
            elif type(x) is int and self.tracing_mode == "symbolic":
                if self.fake_tensor_mode.shape_env is None:
                    raise AssertionError(
                        "shape_env should be set if tracing with 'symbolic'"
                    )
                return self.fake_tensor_mode.shape_env.create_symintnode(
                    self.fake_tensor_mode.shape_env.create_symbol(
                        x, source, positive=None
                    ),
                    hint=x,
                    source=source,
                )
            elif isinstance(x, torch.ScriptObject) or is_opaque_value(x):
                if is_opaque_value_type(
                    type(x)  # pyrefly: ignore[bad-argument-type]
                ):
                    return x
                return torch._library.fake_class_registry.maybe_to_fake_obj(
                    self.fake_tensor_mode, x
                )

            if isinstance(x, FakeScriptObject):
                raise AssertionError(
                    f"ScriptObject {x} has been fakified. Cannot wrap_fake it again."
                )
            return x