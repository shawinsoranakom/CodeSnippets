def gen_unstructured(
        self, f: NativeFunction, g: NativeFunctionsGroup | None = None
    ) -> str | None:
        with native_function_manager(f):
            inplace_meta = False
            gets_out_inplace_wrapper = False
            if not self.backend_index.has_kernel(f):
                if (
                    self.backend_index.dispatch_key == DispatchKey.Meta
                    and f.func.kind() is SchemaKind.inplace
                    and
                    # Defer to composites for meta implementation
                    not f.has_composite_kernel
                    and
                    # Inplace list operations are not supported
                    len(f.func.returns) == 1
                ):
                    inplace_meta = True
                elif (
                    not self.backend_index.use_out_as_primary
                    and g is not None
                    and gets_generated_out_inplace_wrapper(f, g, self.backend_index)
                ):
                    # We want to generate inplace/out wrappers, that don't have a kernel for the backend.
                    gets_out_inplace_wrapper = True
                else:
                    return None
            if f.manual_kernel_registration:
                return None

            if (
                self.target is Target.REGISTRATION
                and not self.selector.is_native_function_selected(f)
            ):
                return None

            sig = self.wrapper_kernel_sig(f)

            name = sig.name()
            returns_type = sig.returns_type().cpp_type()
            args = sig.arguments()
            args_str = ", ".join(a.defn() for a in args)

            # See Note [Direct dispatch bindings]
            cpp_sig_group = CppSignatureGroup.from_native_function(
                f, method=False, fallback_binding=False
            )

            # TODO: dedupe this with the structured codegen
            if self.target is Target.NAMESPACED_DECLARATION:
                result = ""
                for cpp_sig in cpp_sig_group.signatures(symint=self.symint):
                    result += f"TORCH_API {cpp_sig.decl()};\n"
                return result
            elif self.target is Target.NAMESPACED_DEFINITION:

                def generate_defn(cpp_sig: CppSignature) -> str:
                    return f"""
{cpp_sig.defn()} {{
return {sig.name()}({", ".join(e.expr for e in translate(cpp_sig.arguments(), sig.arguments()))});
}}
"""

                result = ""
                for cpp_sig in cpp_sig_group.signatures(symint=self.symint):
                    result += generate_defn(cpp_sig)
                return result

            elif self.target is Target.ANONYMOUS_DEFINITION:
                # short circuit for inplace_meta
                if inplace_meta:
                    if f.func.arguments.self_arg is None:
                        raise AssertionError(
                            "Expected self_arg to be non-None for inplace_meta"
                        )
                    self_arg_name = f.func.arguments.self_arg.argument.name
                    # TODO: handle in place on tensor list
                    return f"""
{returns_type} {name}({args_str}) {{
  TORCH_CHECK_NOT_IMPLEMENTED({self_arg_name}.is_meta(),
    "Cannot inplace into non-meta tensor with meta tensor argument");
  return {self_arg_name};
}}
"""

                # short circuit for generated inplace/out wrappers
                if gets_out_inplace_wrapper:
                    return self.gen_out_inplace_wrapper(f, g)

                metadata = self.backend_index.get_kernel(f)
                if metadata is None:
                    return None
                if self.class_method_name is None:
                    impl_name = f"{metadata.cpp_namespace}::{metadata.kernel}"
                else:
                    impl_name = f"{metadata.cpp_namespace}::{self.class_method_name}::{metadata.kernel}"

                kernel_sig = kernel_signature(f, self.backend_index)

                args_exprs_str = ", ".join(
                    e.expr
                    for e in translate(
                        sig.arguments(), kernel_sig.arguments(), method=False
                    )
                )

                device_check = "  // No device check\n"
                # Backends that require device guards presumably also require device checks.
                if self.backend_index.device_guard:
                    device_check_args = itertools.chain(
                        f.func.arguments.out, f.func.arguments.flat_positional
                    )
                    device_check = RegisterDispatchKey.gen_device_check(
                        f.device_check, list(device_check_args), name
                    )

                device_guard = "// DeviceGuard omitted"  # default
                if f.device_guard and self.backend_index.device_guard:
                    has_tensor_options = any(
                        isinstance(a, TensorOptionsArguments)
                        for a in f.func.arguments.non_out
                    )
                    if has_tensor_options:
                        # kernel is creating a tensor
                        device_guard = """
  const DeviceGuard device_guard(device_or_default(device));"""

                        # CUDA requires special handling
                        if is_cuda_dispatch_key(self.backend_index.dispatch_key):
                            device_guard = f"globalContext().lazyInitDevice(c10::DeviceType::CUDA);\n{device_guard}"
                    else:
                        # kernel is operating on existing tensors

                        # There is precedence for which argument we use to do
                        # device guard.  This describes the precedence order.
                        self_arg = (
                            [f.func.arguments.self_arg.argument]
                            if f.func.arguments.self_arg is not None
                            else []
                        )
                        candidate_args = itertools.chain(
                            self_arg,
                            f.func.arguments.out,
                            f.func.arguments.flat_positional,
                        )

                        # Only tensor like arguments are eligible
                        device_of = next(
                            (
                                f"{a.name}"
                                for a in candidate_args
                                if a.type.is_tensor_like()
                            ),
                            None,
                        )
                        if device_of is not None:
                            device_guard = f"const OptionalDeviceGuard device_guard(device_of({device_of}));"

                return f"""\
namespace {{

{returns_type} {name}({args_str}) {{
  {device_check}

  {device_guard}
  return {impl_name}({args_exprs_str});
}}

}} // anonymous namespace
"""

            elif self.target is Target.REGISTRATION:
                if f.manual_kernel_registration or self.skip_dispatcher_op_registration:
                    return None
                else:
                    payload = f"TORCH_FN({name})"
                    return f'm.impl("{f.func.name}",\n{payload});\n'
            else:
                assert_never(self.target)