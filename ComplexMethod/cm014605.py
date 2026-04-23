def gen_class_set_output_body(self, k: SchemaKind, maybe_create_proxy: bool) -> str:
        if self.backend_index.dispatch_key in [
            DispatchKey.CUDA,
            DispatchKey.MPS,
            DispatchKey.XPU,
            DispatchKey.CompositeExplicitAutogradNonFunctional,
        ]:
            maybe_set_guard = """
auto current_device = guard_.current_device();
if (C10_UNLIKELY(current_device.has_value())) {
  TORCH_INTERNAL_ASSERT(*current_device == options.device(),
    "structured kernels don't support multi-device outputs");
} else {
  guard_.reset_device(options.device());
}
"""
            maybe_set_guard_line = maybe_set_guard + "\n"
        else:
            maybe_set_guard_line = maybe_set_guard = ""

        if maybe_create_proxy:
            create_proxy = """
auto maybe_proxy = maybe_create_proxy(out, sizes, strides, options);
if (C10_UNLIKELY(maybe_proxy.has_value())) {
    proxy_outputs_[output_idx] = std::move(maybe_proxy).value();
}
"""
        else:
            create_proxy = ""

        if k is SchemaKind.functional:
            if self.backend_index.dispatch_key not in (
                DispatchKey.Meta,
                DispatchKey.CPU,
                DispatchKey.CUDA,
                DispatchKey.MPS,
                DispatchKey.XPU,
                DispatchKey.MTIA,
                DispatchKey.CompositeExplicitAutogradNonFunctional,
            ):
                raise AssertionError(
                    f"Unexpected dispatch key {self.backend_index.dispatch_key} "
                    "for functional schema"
                )
            return f"""{maybe_set_guard_line}
outputs_[output_idx] = create_out(sizes, strides, options);"""
        elif k is SchemaKind.inplace:
            return f"""{maybe_set_guard_line}
const auto& out = outputs_[output_idx].get();
check_inplace(out, sizes, options);
{create_proxy}"""
        elif k is SchemaKind.out:
            return f"""{maybe_set_guard_line}
const auto& out = outputs_[output_idx].get();
resize_out(out, sizes, strides, options);
{create_proxy}"""
        elif k is SchemaKind.mutable or k is SchemaKind.scratch:
            raise AssertionError(
                f"{k} structured operators are currently not supported"
            )
        else:
            assert_never(k)