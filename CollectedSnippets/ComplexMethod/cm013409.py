def replace_ph(x: object) -> object:
                nonlocal cnt
                cnt += 1
                param = sig.parameters[name]
                default: tuple[Any, ...] = (
                    () if param.default is inspect.Parameter.empty else (param.default,)
                )
                out = self.create_proxy(
                    "placeholder", f"{name}_{str(cnt)}", default, {}
                )
                if isinstance(x, PHBase):
                    if x != PH:
                        # Transfer attrs in the case where you're using a placeholder other
                        # than the singleton PH (PH has no attributes to transfer).
                        # Proxies were created out of the placeholders.
                        # Transfer any metadata (put on the placeholders in the form of
                        # attributes set by the user) from the placeholder to the
                        # underlying nodes (the proxy is unwrapped by the user, but
                        # the metadata should hold).
                        _transfer_attrs(fr=x, to=out.node)

                    return out
                # Union[int, bool] == bool in Python <= 3.6
                if (
                    type(x) is bool
                    or type(x) in base_types
                    and type(x) is not torch.Tensor
                ):
                    torch._assert(
                        out == x,
                        f"{name} has been specialized to have value {x} but got another value",
                    )
                elif x is None:
                    args = (
                        out,
                        f"{name} has been specialized to have value None but got another value",
                    )
                    self.create_proxy("call_function", _assert_is_none, args, {})
                else:
                    warnings.warn(
                        f"Was not able to add assertion to guarantee correct input {name} to "
                        f"specialized function. It is up to the user to make sure that your inputs match the "
                        f"inputs you specialized the function with."
                    )

                return x