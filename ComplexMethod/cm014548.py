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