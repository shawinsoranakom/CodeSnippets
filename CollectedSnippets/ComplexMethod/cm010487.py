def validate(x: T) -> T | FakeTensor:
            if not isinstance(x, Tensor):
                return x

            nonlocal flat_arg_fake_tensors
            if not self.is_our_fake(x):
                if hasattr(func, "tags") and torch.Tag.inplace_view in func.tags:
                    args, kwargs = pytree.tree_unflatten(flat_args, args_spec)
                    raise AssertionError(
                        f"Can't call metadata mutating ops on non-Fake Tensor inputs. Found in {render_call(func, args, kwargs)}"
                    )
                allow_non_fake_inputs = (
                    self.allow_non_fake_inputs
                    if fake_tensor_tls.allow_non_fake_inputs_override is None
                    else fake_tensor_tls.allow_non_fake_inputs_override
                )
                if not allow_non_fake_inputs:
                    if isinstance(x, FakeTensor) and x.fake_mode is not self:
                        raise AssertionError(
                            f"Mixing fake modes NYI x.fake_mode={x.fake_mode} vs self={self}"
                        )
                    args, kwargs = pytree.tree_unflatten(flat_args, args_spec)
                    raise AssertionError(
                        f"Please convert all Tensors to FakeTensors first or instantiate FakeTensorMode "
                        f"with 'allow_non_fake_inputs'. Found in {render_call(func, args, kwargs)}"
                    )

                out = converter.from_real_tensor(self, x)
            else:
                out = x

            flat_arg_fake_tensors.append(out)
            return out