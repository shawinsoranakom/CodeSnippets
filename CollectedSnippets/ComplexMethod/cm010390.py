def generate_ttir(
    kernel: "TritonKernelType",
    kwargs: dict[str, Any],
    tma_descriptor_metadata: TMADescriptorMetadata,
) -> tuple["TritonIRModule", list[str]]:
    """
    Uses Triton's internal code generation to create TTIR
    """
    import sympy
    import triton
    import triton.runtime.jit
    from triton.compiler.compiler import ASTSource
    from triton.runtime.autotuner import Autotuner
    from triton.runtime.jit import JITFunction

    from torch._inductor.utils import (
        get_triton_attrs_descriptor_version,
        triton_version_uses_attrs_dict,
        TritonAttrsDescriptorVersion,
    )
    from torch.utils._triton import has_triton_tensor_descriptor_host_tma

    triton_version = get_triton_attrs_descriptor_version()

    import torch._inductor.ir
    from torch._subclasses.fake_tensor import FakeTensor

    if isinstance(kernel, Autotuner):
        if len(kernel.configs) > 0:
            # If we are autotuning, then it doesn't matter which version gets
            # picked for tracing purposes, so lets pick the first one
            kwargs = {**kwargs, **kernel.configs[0].kwargs}
        kernel = kernel.fn

    if not isinstance(kernel, JITFunction):
        raise AssertionError(f"Expected kernel to be a JITFunction, got {type(kernel)}")

    context = triton._C.libtriton.ir.context()
    target = triton.runtime.driver.active.get_current_target()
    backend = triton.compiler.compiler.make_backend(target)
    options = backend.parse_options({})

    # ignore backend-specific kwargs same way as in the native Triton code
    # https://github.com/triton-lang/triton/blob/a6bb57d6285e723c58e87dd7cba263db6efff789/python/triton/runtime/jit.py#L594-L596
    # why this is important for user-defined Triton kernels on AMD: https://github.com/pytorch/pytorch/issues/140800
    for name in list(kwargs):
        if name not in kernel.arg_names and name in options.__dict__:
            kwargs.pop(name)

    if len(kwargs) != len(kernel.arg_names):
        raise ValueError(
            "Incorrect number of arguments passed to kernel: "
            f"passed {list(kwargs.keys())}, expected {kernel.arg_names}."
        )

    # Replace all SymExprs with a regular value for TTIR generation
    # Replace all FakeTensor/TensorBox with real tensors
    # These replacements are needed for triton's type, key and config functions
    ordered_args: dict[str, Any] = {}
    for name in kernel.arg_names:
        a = kwargs[name]
        if isinstance(a, (torch.SymInt, torch.SymFloat, torch.SymBool, sympy.Expr)):
            ordered_args[name] = 2
        elif (
            stable_meta := maybe_unpack_tma_stable_metadata(
                # pyrefly: ignore [bad-argument-type]
                tma_descriptor_metadata.get(name, None)
            )
        ) is not None:
            from triton.tools.tensor_descriptor import TensorDescriptor

            block_shape = stable_meta[0]
            with torch._C._DisableTorchDispatch():
                # need 16-byte aligned strides
                elements_per_dim = max(1, 16 // a.dtype.itemsize)
                base_tensor = torch.empty(
                    [elements_per_dim] * len(block_shape), dtype=a.dtype
                )

            ordered_args[name] = TensorDescriptor.from_tensor(base_tensor, block_shape)
        elif isinstance(a, (FakeTensor, torch._inductor.ir.TensorBox)):
            with torch._C._DisableTorchDispatch():
                ordered_args[name] = torch.empty(2, dtype=a.dtype)
        else:
            ordered_args[name] = a

    def is_stable_tensor_descriptor_arg(arg: Any) -> bool:
        if has_triton_tensor_descriptor_host_tma():
            from triton.tools.tensor_descriptor import TensorDescriptor

            if isinstance(arg, TensorDescriptor):
                return True
        return False

    def _is_constexpr_or_none(name: str, arg: Any) -> bool:
        param_idx = kernel.arg_names.index(name)
        return kernel.params[param_idx].is_constexpr or arg is None

    # Note: one would expect that each input to the triton kernel maps to
    # one input parameter in the TTIR. This is _not_ true for TMA descriptors:
    # one TMA descriptor gets converted into:
    #   * one TMA descriptor input
    #   * N strides, for a rank-N tensor
    #   * N sizes, for a rank-N tensor
    # To account for this, we inject some fake arg names as placeholders for
    # the stride and size parameters.
    #
    # Additionally, tensors and scalars are both included as TTIR parameters,
    # whereas `constexpr` are inlined, and None are excluded. We both preserve
    # scalars and tensors as this matters for "odd" ordering,
    # eg. [tensor, scalar, tensor].
    def get_arg_names(name: str, arg: Any) -> list[str]:
        if _is_constexpr_or_none(name, arg):
            return []

        if is_stable_tensor_descriptor_arg(arg):
            stable_meta = maybe_unpack_tma_stable_metadata(
                tma_descriptor_metadata[name]
            )
            if stable_meta is None:
                raise AssertionError(f"Failed to unpack stable TMA metadata for {name}")
            block_shape = stable_meta[0]
            tensor_rank = len(block_shape)
            names = [name]
            names.extend(name + f" STRIDE PLACEHOLDER {i}" for i in range(tensor_rank))
            names.extend(name + f" SIZE PLACEHOLDER {i}" for i in range(tensor_rank))
            return names

        return [name]

    ordered_arg_names = list(
        itertools.chain.from_iterable(
            get_arg_names(name, arg) for name, arg in ordered_args.items()
        )
    )

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

    specialization = _get_specialization(ordered_args.values())
    # Triton explicitly interprets ASTSource.constants entries as constexpr
    # Thus, only None and arguments marked `is_constexpr` should be treated as such.
    constants = {
        name: arg
        for name, arg in ordered_args.items()
        if _is_constexpr_or_none(name, arg)
    }

    if (mangle_type := getattr(triton.runtime.jit, "mangle_type", None)) is not None:

        def get_signature_value(idx: int, arg: Any) -> str:
            if kernel.params[idx].is_constexpr:
                return "constexpr"
            # pyrefly: ignore [not-callable]
            result = mangle_type(arg)
            # Workaround for Triton i1/u1 AOTI bug: PyTorch stores bool
            # tensors as uint8 (1 byte per element), but *i1/*u1 causes
            # the compiled kernel to generate bit-packed loads. Use *u8
            # so loads correctly read 1 byte per element.
            if result in ("*i1", "*u1"):
                result = "*u8"
            return result

    else:

        def get_signature_value(idx: int, arg: Any) -> str:
            return kernel._type_of(kernel.key_of(arg))

    if triton_version_uses_attrs_dict():
        # In newer versions of Triton, the signature includes constexpr args
        signature = {
            name: get_signature_value(i, arg)
            for i, (name, arg) in enumerate(ordered_args.items())
        }
    else:
        # In older versions of Triton, the signature does not include constexpr args
        constexprs = [p.num for p in kernel.params if p.is_constexpr]
        signature = {
            name: get_signature_value(i, arg)
            for i, (name, arg) in enumerate(ordered_args.items())
            if i not in constexprs
        }

    triton._C.libtriton.ir.load_dialects(context)
    backend.load_dialects(context)

    src = ASTSource(kernel, signature, constants, specialization)

    # Triton changes ASTSource.make_ir to take 3/4 arguments. Handle
    # backward compatibility here.
    make_ir_sig_params = len(inspect.signature(src.make_ir).parameters)
    get_codegen_implementation_sig_params = len(
        inspect.signature(backend.get_codegen_implementation).parameters
    )
    if make_ir_sig_params == 2:
        ttir_module = src.make_ir(options, context)
    elif make_ir_sig_params == 3:
        codegen_fns = backend.get_codegen_implementation()

        ttir_module = src.make_ir(options, codegen_fns, context)
    elif make_ir_sig_params == 4:
        codegen_args = [options] if get_codegen_implementation_sig_params == 1 else []

        codegen_fns = backend.get_codegen_implementation(*codegen_args)
        module_map = backend.get_module_map()

        ttir_module = src.make_ir(options, codegen_fns, module_map, context)
    else:
        codegen_args = [options] if get_codegen_implementation_sig_params == 1 else []

        codegen_fns = backend.get_codegen_implementation(*codegen_args)
        module_map = backend.get_module_map()

        ttir_module = src.make_ir(target, options, codegen_fns, module_map, context)
    if not ttir_module.verify():
        raise RuntimeError("Verification for TTIR module has failed")

    return ttir_module, ordered_arg_names