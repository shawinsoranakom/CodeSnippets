def gen_source_files(
    *,
    native_functions: Sequence[NativeFunction],
    grouped_native_functions: Sequence[NativeFunction | NativeFunctionsGroup],
    structured_native_functions: Sequence[NativeFunctionsGroup],
    view_groups: Sequence[NativeFunctionsViewGroup],
    selector: SelectiveBuilder,
    static_dispatch_idx: list[BackendIndex],
    backend_indices: dict[DispatchKey, BackendIndex],
    aoti_fm: FileManager,
    core_fm: FileManager,
    cpu_vec_fm: FileManager,
    cpu_fm: FileManager,
    device_fms: dict[str, FileManager],
    dispatch_keys: Sequence[DispatchKey],
    functions_keys: set[DispatchKey],
    rocm: bool,
    force_schema_registration: bool,
    per_operator_headers: bool,
    skip_dispatcher_op_registration: bool,
    update_aoti_c_shim: bool,
    aoti_backends: set[DispatchKey | None],
    extend_aoti_c_shim: bool,
) -> None:
    extra_cuda_headers = """\
#include <c10/cuda/CUDAGuard.h>
#include <ATen/cuda/ATenCUDAGeneral.h>
#include <ATen/cuda/CUDADevice.h>
#include <ATen/cuda/CUDAContext.h>"""
    if rocm:
        extra_cuda_headers = """\
#include <c10/hip/HIPGuard.h>
#include <ATen/hip/ATenHIPGeneral.h>
#include <ATen/hip/HIPDevice.h>
#include <ATen/hip/HIPContext.h>"""

    for dispatch_key in dispatch_keys:
        fm = file_manager_from_dispatch_key(dispatch_key, device_fms, cpu_fm)
        if per_operator_headers:

            def operator_headers() -> list[str]:
                headers = []
                for g in grouped_native_functions:
                    is_registered = False
                    if backend_index.has_kernel(g):
                        is_registered = True
                    # The above has_kernel test on a group will only test for
                    # the existence of out dispatch, because that's how
                    # structured kernels work. But sometimes functions can be
                    # grouped but not be structured, and then you need to check
                    # each individual piece, as they may have manual dispatch
                    # entries.
                    elif isinstance(g, NativeFunctionsGroup) and any(
                        backend_index.has_kernel(fn) for fn in g.functions()
                    ):
                        is_registered = True
                    # TODO: this condition is a bit questionable
                    # (It has to do with the fact that structured kernels get generated kernels
                    # to the Meta + CompositeExplicitAutogradNonFunctional keys).
                    elif g.structured and dispatch_key in (
                        DispatchKey.Meta,
                        DispatchKey.CompositeExplicitAutogradNonFunctional,
                    ):
                        is_registered = True
                    if not is_registered:
                        continue

                    headers.append(f"#include <ATen/ops/{g.root_name}_native.h>")
                    if (
                        dispatch_key
                        == DispatchKey.CompositeExplicitAutogradNonFunctional
                    ):
                        headers.append(f"#include <ATen/ops/{g.root_name}.h>")
                    if dispatch_key in functions_keys:
                        headers.append(
                            f"#include <ATen/ops/{g.root_name}_{dispatch_namespace}_dispatch.h>"
                        )

                return sorted(set(headers))

        else:

            def operator_headers() -> list[str]:
                headers = ["#include <ATen/NativeFunctions.h>"]
                if dispatch_key == DispatchKey.CompositeExplicitAutogradNonFunctional:
                    headers.append("#include <ATen/Functions.h>")
                if dispatch_key in functions_keys:
                    headers.append(f"#include <ATen/{dispatch_key!s}Functions.h>")
                return headers

        backend_index = backend_indices[dispatch_key]
        ns_grouped_native_functions = defaultdict(list)
        for grouped_native_function in grouped_native_functions:
            namespace = (
                grouped_native_function.namespace
                if isinstance(grouped_native_function, NativeFunction)
                else grouped_native_function.functional.namespace
            )
            ns_grouped_native_functions[namespace].append(grouped_native_function)

        dispatch_namespace = str(dispatch_key).lower()

        # CompositeImplicitAutogradNestdTensor does not currently user the helpers generated
        # compilation will fail when `-Werror=unused-function` flag is set
        gen_dispatch_helpers: bool = (
            dispatch_key != DispatchKey.CompositeImplicitAutogradNestedTensor
        )

        register_dispatch_key_base_env = {
            "extra_cuda_headers": extra_cuda_headers
            if is_cuda_dispatch_key(dispatch_key)
            else "",
            "external_backend_headers": "",
            "dispatch_headers": dest.gen_registration_headers(
                backend_index, per_operator_headers, rocm
            ),
            # ops_headers *could* be sharded, but doesn't seem necessary?
            "ops_headers": operator_headers(),
            "dispatch_helpers": (
                dest.gen_registration_helpers(backend_index)
                if gen_dispatch_helpers
                else []
            ),
        }

        def register_dispatch_key_env_callable(
            gnf: NativeFunction | NativeFunctionsGroup,
        ) -> dict[str, list[str]]:
            return {
                "dispatch_definitions": get_native_function_definitions(
                    fm=fm,  # noqa: F821
                    grouped_native_functions=[gnf],
                    dispatch_key=dispatch_key,
                    backend_idx=backend_index,
                    selector=selector,
                    rocm=rocm,
                    symint=True,
                    skip_dispatcher_op_registration=skip_dispatcher_op_registration,
                    gen_dispatch_helpers=gen_dispatch_helpers,
                )
            }

        fm.write_sharded_with_template(
            f"Register{dispatch_key}.cpp",
            "RegisterDispatchKey.cpp",
            grouped_native_functions,
            key_fn=lambda x: x.root_name,
            env_callable=register_dispatch_key_env_callable,
            num_shards=4 if dispatch_key == DispatchKey.CPU else 1,
            base_env=register_dispatch_key_base_env,
            sharded_keys={"dispatch_definitions"},
        )

        for g in structured_native_functions:
            if not g.out.ufunc_inner_loop or not is_ufunc_dispatch_key(dispatch_key):
                continue
            name = g.functional.func.name.name
            if dispatch_key is DispatchKey.CPU:
                if fm is not cpu_fm:
                    raise AssertionError("Expected fm to be cpu_fm for DispatchKey.CPU")
                fm.write_with_template(
                    f"UfuncCPU_{name}.cpp",
                    "UfuncCPU.cpp",
                    lambda: {
                        "meta_declaration": compute_meta_function_declaration(g),
                        "native_declaration": dest.compute_native_function_declaration(
                            g, backend_indices[dispatch_key]
                        ),
                        "native_definitions": dest.compute_ufunc_cpu(g),
                    },
                )
                cpu_vec_fm.write_with_template(
                    f"UfuncCPUKernel_{name}.cpp",
                    "UfuncCPUKernel.cpp",
                    lambda: {
                        "name": name,
                        "native_definitions": dest.compute_ufunc_cpu_kernel(g),
                    },
                )
            elif dispatch_key is DispatchKey.CUDA:
                cuda_headers = "#include <ATen/native/cuda/Loops.cuh>"
                if rocm:
                    cuda_headers = "#include <ATen/native/hip/Loops.cuh>"
                fm.write_with_template(
                    f"UfuncCUDA_{name}.cu",
                    "UfuncCUDA.cu",
                    lambda: {
                        "name": name,
                        "cuda_headers": cuda_headers,
                        "meta_declaration": compute_meta_function_declaration(g),
                        "native_declaration": dest.compute_native_function_declaration(
                            g, backend_indices[dispatch_key]
                        ),
                        "native_definitions": dest.compute_ufunc_cuda(g),
                    },
                )
            else:
                raise AssertionError(f"unrecognized {dispatch_key} for ufunc")

        del fm

    gen_aoti_c_shim_files(
        aoti_fm=aoti_fm,
        aoti_backends=aoti_backends,
        native_functions=native_functions,
        backend_indices=backend_indices,
        structured_native_functions=structured_native_functions,
        extra_cuda_headers=extra_cuda_headers,
        update_aoti_c_shim=update_aoti_c_shim,
        extend_aoti_c_shim=extend_aoti_c_shim,
    )

    # BackendSelect is generated specially
    def gen_backend_select() -> dict[str, list[str]]:
        relevant_fns = [
            fn for fn in native_functions if needs_backend_select(fn, selector)
        ]
        return {
            "ops_headers": [
                f"#include <ATen/ops/{fn.root_name}_ops.h>" for fn in relevant_fns
            ],
            "backend_select_method_definitions": list(
                mapMaybe(
                    ComputeBackendSelect(Target.DEFINITION, selector), relevant_fns
                )
            ),
            "backend_select_function_registrations": list(
                mapMaybe(
                    ComputeBackendSelect(Target.REGISTRATION, selector), relevant_fns
                )
            ),
        }

    cpu_fm.write("RegisterBackendSelect.cpp", gen_backend_select)

    schema_selector = selector
    if force_schema_registration:
        schema_selector = SelectiveBuilder.get_nop_selector()

    (
        aten_schema_registrations,
        schema_registrations,
    ) = get_native_function_schema_registrations(
        native_functions=native_functions, schema_selector=schema_selector
    )
    cpu_fm.write(
        "RegisterSchema.cpp",
        lambda: {
            "aten_schema_registrations": []
            if skip_dispatcher_op_registration
            else aten_schema_registrations,
            "schema_registrations": []
            if skip_dispatcher_op_registration
            else schema_registrations,
        },
    )

    def key_func(
        fn: NativeFunction | NativeFunctionsGroup | NativeFunctionsViewGroup,
    ) -> str:
        return fn.root_name

    cpu_fm.write_sharded(
        "Operators.cpp",
        native_functions,
        key_fn=key_func,
        env_callable=lambda fn: {
            "operator_headers": [f"#include <ATen/ops/{fn.root_name}.h>"],
            "definitions": [
                ComputeOperators(
                    Target.DEFINITION,
                    static_dispatch_backend_indices=static_dispatch_idx,
                )(fn)
            ],
        },
        base_env={
            "static_dispatch_extra_headers": static_dispatch_extra_headers(
                static_dispatch_idx
            ),
        },
        num_shards=5,
        sharded_keys={
            "operator_headers",
            "definitions",
            "static_dispatch_extra_headers",
        },
    )

    cpu_fm.write("Functions.cpp", dict)

    core_fm.write("TensorMethods.cpp", dict)

    core_fm.write(
        "ATenOpList.cpp",
        lambda: {
            "aten_ops": list(mapMaybe(compute_aten_op, native_functions)),
        },
    )

    def gen_op_headers(
        g: NativeFunction | NativeFunctionsGroup | NativeFunctionsViewGroup,
    ) -> list[str]:
        if isinstance(g, NativeFunctionsViewGroup):
            # view ops always get a functionalization kernel
            headers = [
                f"#include <ATen/ops/{g.view.root_name}_native.h>",
                f"#include <ATen/ops/{g.view.root_name}_ops.h>",
            ]
            if g.view_copy is not None:
                headers += [
                    f"#include <ATen/ops/{g.view_copy.root_name}_native.h>",
                    f"#include <ATen/ops/{g.view_copy.root_name}_ops.h>",
                ]
            return headers
        elif isinstance(g, NativeFunctionsGroup):
            headers = [
                f"#include <ATen/ops/{g.functional.root_name}_native.h>",
                f"#include <ATen/ops/{g.functional.root_name}_ops.h>",
                f"#include <ATen/ops/{g.out.root_name}_native.h>",
                f"#include <ATen/ops/{g.out.root_name}_ops.h>",
            ]
            if g.inplace is not None:
                headers += [
                    f"#include <ATen/ops/{g.inplace.root_name}_native.h>",
                    f"#include <ATen/ops/{g.inplace.root_name}_ops.h>",
                ]
            if g.mutable is not None:
                headers += [
                    f"#include <ATen/ops/{g.mutable.root_name}_native.h>",
                    f"#include <ATen/ops/{g.mutable.root_name}_ops.h>",
                ]
            return headers
        else:
            return [
                f"#include <ATen/ops/{g.root_name}_native.h>",
                f"#include <ATen/ops/{g.root_name}_ops.h>",
            ]

    def functionalization_env_callable(
        g: NativeFunction | NativeFunctionsGroup | NativeFunctionsViewGroup,
    ) -> dict[str, list[str]]:
        return {
            "ops_headers": gen_op_headers(g),
            "func_definitions": gen_functionalization_definition(
                selector,
                g,
            ),
            "func_registrations": gen_functionalization_registration(
                selector,
                g,
                backend_indices[DispatchKey.CompositeImplicitAutograd],
            ),
        }

    all_groups: list[
        NativeFunction | NativeFunctionsGroup | NativeFunctionsViewGroup
    ] = list(structured_native_functions) + list(
        view_groups  # type: ignore[assignment, arg-type, operator]
    )
    # Note: all operators that functionalization needs to handle (mutable and aliasing ops) should be grouped properly.
    # The only reason we really need to deal with direct NativeFunctions here (instead of the groups) is because:
    # (1) We can provide better error checking (error out if someone introduces a mutable op that doesn't obey the grouping logic)
    # (2) functionalization needs to manually register CompositeImplicitAutograd kernels, which might not be grouped.
    #     Although this could go away long-term if we add a dedicated dispatch key for decompositions.
    structured_map: dict[OperatorName, NativeFunction] = {
        f.func.name: f
        for f in concatMap(lambda g: list(g.functions()), structured_native_functions)
    }
    view_map: dict[OperatorName, NativeFunction] = {
        f.func.name: f for f in concatMap(lambda g: list(g.functions()), view_groups)
    }
    all_groups.extend(
        f
        for f in native_functions
        if f.func.name not in structured_map and f.func.name not in view_map
    )

    cpu_fm.write_sharded(
        "RegisterFunctionalization.cpp",
        all_groups,
        key_fn=key_func,
        env_callable=functionalization_env_callable,
        num_shards=4,
        sharded_keys={
            "ops_headers",
            "func_definitions",
            "func_registrations",
            "func_add_back_views_definitions",
            "func_add_back_views_registrations",
        },
    )

    cpu_fm.write(
        "FunctionalInverses.h",
        lambda: {
            "view_inverse_declarations": list(
                mapMaybe(
                    lambda g: gen_functionalization_view_inverse_declaration(
                        selector, g
                    ),
                    view_groups,
                )
            )
        },
    )

    cpu_fm.write(
        "ViewMetaClasses.h",
        lambda: {
            "view_meta_declarations": list(
                concatMap(
                    lambda g: gen_functionalization_view_meta_classes_decl(selector, g),
                    view_groups,
                )
            )
        },
    )

    cpu_fm.write(
        "ViewMetaClasses.cpp",
        lambda: {
            "view_meta_implementations": list(
                concatMap(
                    lambda g: gen_functionalization_view_meta_classes_impl(selector, g),
                    view_groups,
                )
            ),
            "op_headers": list(concatMap(gen_op_headers, view_groups)),
        },
    )

    # Note [view_copy NativeFunctions]
    # Every view operator in native_functions.yaml that is not CompositeImplicitAutograd
    # needs to have a corresponding non-aliasing {view}_copy variant.
    # Backends that use functionalization and don't know how to handle aliasing ops
    # are expected to implement kernels for these {view}_copy kernels instead.
    # The code for {view}_copy operators in core is pretty boilerplate-heavy however,
    # so we codegen the following:
    # (1) A CompositeExplicitAutogradNonFunctional kernel for every {view}_copy operator.
    #     These are never explicitly invoked by the functionalization pass,
    #     but they could theoretically be called from user code (I added these kernels for completeness,
    #     since the ops are part of the public API).
    # (2) A derivative formula for every {view}_copy operator
    #     {view}_copy operators can reuse the same derivative formulas as their {view} op counterparts,
    #     so rather than stamping all of the entries out in derivatives.yaml,
    #     we codegen them in.
    #     This is similar to how autograd codegen doesn't require inplace ops to have a derivatives.yaml entry.
    cpu_fm.write(
        "CompositeViewCopyKernels.cpp",
        lambda: {
            "ops_headers": [
                "\n".join(
                    f"#include <ATen/ops/{f.root_name}_ops.h>\n"
                    # NB: this include is important as it ensures we
                    # set the visibility on generated view_copy kernels
                    # correctly
                    f"#include <ATen/ops/{f.root_name}_native.h>"
                    for f in (
                        [g.view] if g.view_copy is None else [g.view, g.view_copy]
                    )
                )
                for g in view_groups
            ]
            + [
                "\n".join(
                    f"#include <ATen/ops/{f.root_name}_ops.h>\n"
                    # NB: this include is also important for correct visibility
                    f"#include <ATen/ops/{f.root_name}_native.h>"
                    for f in [g.inplace, g.mutable, g.functional]
                    if f is not None and "generated" not in f.tags
                )
                for g in structured_native_functions
            ],
            "CompositeViewCopyKernel_Definitions": list(
                mapMaybe(
                    GenCompositeViewCopyKernel(
                        backend_indices[
                            DispatchKey.CompositeExplicitAutogradNonFunctional
                        ]
                    ),
                    view_groups,
                )
            ),
            "GeneratedCompositeFunctional_Definitions": list(
                mapMaybe(
                    gen_composite_functional_kernel,
                    structured_native_functions,
                )
            ),
            "GeneratedCompositeOut_Definitions": list(
                mapMaybe(
                    gen_composite_out_kernel,
                    structured_native_functions,
                )
            ),
        },
    )