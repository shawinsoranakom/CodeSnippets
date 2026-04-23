def write_kernel_dependencies(
        kernel: Any,
        written_constexpr_vars: set[str],
        written_nested_kernels: set[str],
    ) -> str:
        """Write out global tl.constexpr vars and nested kernel dependencies."""
        result = ""
        jit_fn = kernel if isinstance(kernel, JITFunction) else kernel.fn
        if not getattr(jit_fn, "fn", None) or not getattr(jit_fn, "src", None):
            return result

        fn_globals = getattr(jit_fn.fn, "__globals__", {})
        src = jit_fn.src
        full_src = src if src.strip().startswith("def ") else "def " + src

        referenced_names: set[str] = set()
        called_names: set[str] = set()
        for node in ast.walk(ast.parse(full_src)):
            if isinstance(node, ast.Name):
                referenced_names.add(node.id)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                called_names.add(node.func.id)

        # Write out global tl.constexpr variables
        for name in referenced_names:
            if name in written_constexpr_vars:
                continue
            val = fn_globals.get(name)

            if isinstance(val, TritonConstexpr) and getattr(val, "value", None):
                result += f"{name} = tl.constexpr({val.value})\n"
            elif isinstance(val, (int, float, str, bool)):
                result += f"{name} = {val!r}\n"
            else:
                continue
            written_constexpr_vars.add(name)

        # Write out nested kernel dependencies
        for name in called_names:
            val = fn_globals.get(name)
            if not isinstance(val, JITFunction) or val is jit_fn:
                continue
            nested_fn_name = get_fn_name(val)
            if nested_fn_name in written_nested_kernels:
                continue
            # Mark as written before recursing to prevent cycles
            written_nested_kernels.add(nested_fn_name)
            result += write_kernel_dependencies(
                val, written_constexpr_vars, written_nested_kernels
            )
            result += generate_custom_triton_kernel(val)

        return result