def gen_class(
        self,
        f: NativeFunction,
        k: SchemaKind,
        *,
        class_name: str,
        parent_class: str,
        generate_super: bool,
    ) -> str:
        if k is SchemaKind.functional:
            output_type = "Tensor"
            output_value = "outputs_[output_idx]"
            proxy_field = ""
        elif k is SchemaKind.inplace:
            output_type = "std::reference_wrapper<Tensor>"
            output_value = "proxy_outputs_[output_idx].has_value() ? *proxy_outputs_[output_idx] : outputs_[output_idx].get()"
            proxy_field = f"std::array<::std::optional<Tensor>, {len(f.func.returns)}> proxy_outputs_;"
        elif k is SchemaKind.out:
            output_type = "std::reference_wrapper<Tensor>"
            output_value = "proxy_outputs_[output_idx].has_value() ? *proxy_outputs_[output_idx] : outputs_[output_idx].get()"
            proxy_field = f"std::array<::std::optional<Tensor>, {len(f.func.returns)}> proxy_outputs_;"
        else:
            raise RuntimeError(f"Unsupported SchemaKind {k}")

        if self.backend_index.dispatch_key == DispatchKey.CUDA:
            guard_field = "c10::cuda::OptionalCUDAGuard guard_;"
        elif (
            self.backend_index.dispatch_key
            == DispatchKey.CompositeExplicitAutogradNonFunctional
        ):
            guard_field = "c10::OptionalDeviceGuard guard_;"
        elif self.backend_index.dispatch_key == DispatchKey.MPS:
            # TODO: Move to OptionalMPSGuard.
            guard_field = "c10::OptionalDeviceGuard guard_;"
        elif self.backend_index.dispatch_key == DispatchKey.XPU:
            guard_field = "c10::OptionalDeviceGuard guard_;"
        elif self.backend_index.dispatch_key == DispatchKey.MTIA:
            guard_field = "c10::OptionalDeviceGuard guard_;"
        else:
            guard_field = ""

        indent = " " * 4
        class_ctor_str = self.gen_class_ctor(k, class_name, len(f.func.returns))
        lines = (
            f"struct {class_name} final : public {parent_class} {{",
            f"{textwrap.indent(class_ctor_str, indent)}",
            f"{textwrap.indent(self.gen_class_set_output_functions(k, parent_class, generate_super), indent)}",
            "    const Tensor& maybe_get_output(int64_t output_idx) override {",
            f"      return {output_value};\n",  # type: ignore[possibly-undefined]  # TODO: audit
            "    }",
            # type: ignore[possibly-undefined]  # TODO: audit
            f"    std::array<{output_type}, {len(f.func.returns)}> outputs_;",
            f"{textwrap.indent(proxy_field, indent)}",  # type: ignore[possibly-undefined]  # TODO: audit
            f"{textwrap.indent(guard_field, indent)}",
            "};",
        )
        return "\n".join(line for line in lines if line)