def write_decl_impl(
    kernels: list[T],
    family_name: str,
    impl_file: str,
    autogen_dir: Path,
    disable_def: str | None = None,
) -> None:
    cpp_file_header = """/*
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
// This file is auto-generated. See "generate_kernels.py"
"""

    kernels.sort()

    implfile_to_kernels: dict[str, list[T]] = collections.defaultdict(list)
    cat_to_kernels: dict[tuple[str, int, int], list[T]] = collections.defaultdict(list)

    dispatch_all = ""
    declarations = cpp_file_header + "#pragma once\n"
    # declarations += f"#ifndef {disable_def}\n"
    declarations += f"""#include {impl_file}\n"""
    declarations += """using namespace PyTorchMemEffAttention;\n"""

    # Declaration of kernel functions
    for k in kernels:
        implfile_to_kernels[k.impl_group].append(k)
        cat_to_kernels[(k.dtype, k.sm_range[0], k.sm_range[1])].append(k)

    for (cat_dt, cat_sm, cat_sm_max), kernels in cat_to_kernels.items():
        declarations += f"// ======== {cat_dt} / sm{cat_sm} ========\n"
        declarations += "\n".join(
            k.cpp_impl.split("{")[0].rstrip() + ";" for k in kernels
        )
        dispatch_category_fn = f"dispatch_{family_name}_{cat_dt}_sm{cat_sm}"
        declarations += (
            f"\n\ntemplate <typename T> void {dispatch_category_fn}(T cb, int cc) {{\n"
        )
        for k in kernels:
            _call = f"cb({k.cpp_class}(), {k.name});\n"
            if k.dispatch_cond is not None:
                _call = f"if ({k.dispatch_cond}) {_call}"
            declarations += f"    {_call}"
        declarations += "}\n\n"
        dispatch_all += f"""
    if (std::is_same_v<DT, {DTYPES[cat_dt]}> && {cat_sm} <= cc && cc <= {cat_sm_max}) {{
        {dispatch_category_fn}(cb, cc);
    }}"""

    declarations += f"""
template <typename DT, typename T>
void dispatch_{family_name}(T cb, int cc = 0) {{
{dispatch_all}
}}
"""
    # declarations += f"#endif // {disable_def}\n"

    # Write declarations to family header
    (autogen_dir / f"{family_name}.h").write_text(declarations)

    for f, f_kernels in implfile_to_kernels.items():
        impl_cu = cpp_file_header
        # impl_cu += f"#ifndef {disable_def}\n"
        impl_cu += f"""#include {impl_file}\n"""
        impl_cu += """using namespace PyTorchMemEffAttention;\n"""
        for k in f_kernels:
            impl_cu += k.cpp_impl
        # impl_cu += f"#endif // {disable_def}\n"
        (autogen_dir / f"{family_name}_{f}.cu").write_text(impl_cu)