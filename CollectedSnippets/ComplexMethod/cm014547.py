def __call__(self, f: NativeFunction) -> str | None:
        if not needs_backend_select(f, self.selector):
            return None

        name = native.name(f.func)
        # BackendSelect can go to Meta, so it must preserve symints
        native_sig = NativeSignature(f.func, symint=True)

        native_tensor_args = [
            a
            for a in native_sig.arguments()
            if isinstance(a.argument, Argument) and a.argument.type.is_tensor_like()
        ]

        dispatcher_sig = DispatcherSignature.from_schema(f.func)

        sig: NativeSignature | DispatcherSignature
        sig = dispatcher_sig
        dispatcher_exprs = dispatcher_sig.exprs()
        dispatch_key = "c10::computeDispatchKey(dtype, layout, device)"

        if self.target is Target.DEFINITION:
            # I don't think there's actually a good reason to generate
            # these two cases differently
            # The first case could probably be improved though- it calls computeDispatchKeySet(),
            # which looks at TLS dispatch keys- there should not be any by the time we reach backend select.
            if native_tensor_args:
                if not f.func.arguments.has_tensor_arg():
                    raise AssertionError(
                        f"Expected function to have tensor args: {f.func}"
                    )
                tensor_args = ", ".join(a.name for a in native_tensor_args)
                compute_dk = f"""\
DispatchKeySet _dk_set = c10::DispatchKeySet({dispatch_key}) | c10::detail::multi_dispatch_key_set({tensor_args});
DispatchKeySet _dk_mask = c10::DispatchKeySet(DispatchKeySet::FULL_AFTER, DispatchKey::BackendSelect);
DispatchKeySet _dk = c10::impl::computeDispatchKeySet(_dk_set, _dk_mask);"""
            else:
                if f.func.arguments.has_tensor_arg():
                    raise AssertionError(
                        f"Expected function to not have tensor args: {f.func}"
                    )
                compute_dk = (
                    f"DispatchKeySet _dk = c10::DispatchKeySet({dispatch_key});"
                )
            return f"""\
// aten::{f.func}
C10_ALWAYS_INLINE
{sig.defn(name)} {{
  {compute_dk}
  return at::_ops::{f.func.name.unambiguous_name()}::redispatch(
      _dk, {", ".join(a.expr for a in dispatcher_exprs)});
}}
"""
        elif self.target is Target.REGISTRATION:
            return f"""m.impl("aten::{f.func.name}", TORCH_FN({name}));"""
        else:
            assert_never(self.target)