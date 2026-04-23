def _get_specialization(args):  # type: ignore[no-untyped-def]
        # Support multiple triton versions.
        # This code basically copies JITFunction.run() logic to get the attrs to construct an ASTSource.
        if triton_version == TritonAttrsDescriptorVersion.V1_COMPILER:
            return kernel._get_config(*args)
        elif triton_version in {
            TritonAttrsDescriptorVersion.V2_BACKENDS,
            TritonAttrsDescriptorVersion.V3_BACKENDS_TUPLE,
        }:
            from triton.backends.compiler import AttrsDescriptor  # noqa: F401

            target = triton.runtime.driver.active.get_current_target()
            backend_ = triton.compiler.compiler.make_backend(target)

            return backend_.get_attrs_descriptor(args, kernel.params)
        else:
            if (
                get_triton_attrs_descriptor_version()
                != TritonAttrsDescriptorVersion.V4_DICT
            ):
                raise AssertionError(
                    f"Expected Triton attrs descriptor version V4_DICT, "
                    f"got {get_triton_attrs_descriptor_version()}"
                )
            # specialize_impl switched to create_specialize_impl in https://github.com/triton-lang/triton/pull/6099
            if hasattr(triton.runtime.jit, "create_specialize_impl"):
                try:
                    # Latest versions of Triton take specialize_extra as an arg to create_specialize_impl
                    specialize_impl = triton.runtime.jit.create_specialize_impl(
                        specialize_extra=backend.get_arg_specialization
                    )
                except TypeError:  # Unknown arg `specialize_extra`
                    # Older versions of Triton take specialize_extra as an arg to specialize_impl
                    specialize_impl = functools.partial(
                        triton.runtime.jit.create_specialize_impl(),
                        specialize_extra=backend.get_arg_specialization,
                    )
            # create_specialize_impl is removed in https://github.com/triton-lang/triton/pull/7771
            # switch to native_specialize_impl instead
            elif hasattr(triton.runtime.jit, "native_specialize_impl"):
                from triton.backends import BaseBackend
                from triton.runtime.jit import native_specialize_impl

                def _native_specialize_impl(
                    arg: Any,
                    is_const: bool = False,
                    specialize_value: bool = True,
                    align: bool = True,
                ) -> Callable:
                    return native_specialize_impl(
                        BaseBackend, arg, is_const, specialize_value, align
                    )

                specialize_impl = _native_specialize_impl
            else:
                from triton.runtime.jit import specialize_impl as specialize_impl_orig

                specialize_impl = functools.partial(
                    specialize_impl_orig,
                    specialize_extra=backend.get_arg_specialization,
                )

            from triton._utils import find_paths_if, get_iterable_path

            # logic is copied from: binder = create_function_from_signature(self.signature, self.params, backend)
            attrvals = []
            for arg, kp in zip(args, kernel.params):
                if kp.is_constexpr:
                    attrvals.append(arg)
                else:
                    spec = specialize_impl(
                        arg,
                        is_const=kp.is_const,
                        specialize_value=not kp.do_not_specialize,
                        align=not kp.do_not_specialize_on_alignment,
                    )
                    # pyrefly: ignore [unsupported-operation]
                    attrvals.append(spec[1])

            attrs = find_paths_if(attrvals, lambda _, x: isinstance(x, str))
            attrs = {
                k: backend.parse_attr(get_iterable_path(attrvals, k)) for k in attrs
            }
            return attrs