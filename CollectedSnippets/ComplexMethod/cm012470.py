def traverse(cur_kernel):
        # here we extract the unqualified names (i.e., not attributes and
        # without prepended module name) loaded in the kernel code, which
        # are matched with the co_names and __globals__ below to codegen
        # the respective imports necessary for the kernel compilation
        unqualified_loads = OrderedSet(
            inst.argval
            for inst in dis.Bytecode(cur_kernel.fn)
            if inst.opname == "LOAD_GLOBAL"
        )
        global_annotations = cur_kernel.fn.__globals__.get("__annotations__", {})
        for symbol_name in cur_kernel.fn.__code__.co_names:
            if symbol_name in symbols_included:
                continue
            if symbol_name in cur_kernel.fn.__globals__:
                symbol = cur_kernel.fn.__globals__[symbol_name]
                if isinstance(symbol, JITFunction):
                    compile_wrapper.newline()
                    compile_wrapper.writeline("@triton.jit")
                    compile_wrapper.splice(symbol.src, strip=True)
                    symbols_included.add(symbol_name)
                    traverse(symbol)
                elif hasattr(triton, "constexpr_function") and isinstance(
                    symbol,
                    triton.runtime.jit.ConstexprFunction,
                ):
                    # Import dtype class if used in type annotations
                    if "dtype" in symbol.src and "dtype" not in symbols_included:
                        dtype_symbol = symbol.fn.__globals__.get("dtype")
                        if (
                            dtype_symbol
                            and hasattr(dtype_symbol, "__module__")
                            and dtype_symbol.__module__.startswith("triton")
                        ):
                            compile_wrapper.writeline(
                                f"from {dtype_symbol.__module__} import dtype as dtype"
                            )
                            symbols_included.add("dtype")
                    compile_wrapper.newline()
                    compile_wrapper.writeline("@triton.constexpr_function")
                    compile_wrapper.splice(symbol.src, strip=True)
                    if symbol_name != symbol.fn.__name__:
                        compile_wrapper.writeline(
                            f"{symbol_name} = {symbol.fn.__name__}"
                        )
                    symbols_included.add(symbol_name)
                    traverse(symbol)
                elif isinstance(symbol, (int, str, bool, constexpr)):
                    compile_wrapper.newline()
                    if isinstance(symbol, constexpr):
                        symbol_str = f"tl.constexpr({symbol.value!r})"
                    else:
                        symbol_str = f"{symbol!r}"
                    if annotation := global_annotations.get(symbol_name):
                        if isinstance(annotation, type):
                            annotation_code = (
                                f": {annotation.__module__}.{annotation.__name__}"
                            )
                        else:
                            annotation_code = f": {annotation!r}"
                        compile_wrapper.writeline(
                            f"{symbol_name}{annotation_code} = {symbol_str}"
                        )
                    else:
                        compile_wrapper.writeline(f"{symbol_name} = {symbol_str}")
                    symbols_included.add(symbol_name)
                elif (
                    symbol_name in unqualified_loads
                    and symbol_name != "tl"  # already imported
                    and hasattr(symbol, "__module__")
                    # only codegen imports from triton; JITFunctions
                    # imported from other modules will be codegened
                    # in the separate branch above
                    and symbol.__module__.startswith("triton")
                ):
                    # a global symbol imported from triton is referenced
                    # without module qualification (i.e., `store` instead
                    # of `tl.store`): need to codegen an import

                    # Triton dtype instances have .name instead of .__name__
                    if isinstance(symbol, triton_dtype):
                        compile_wrapper.writeline(f"{symbol_name} = tl.{symbol.name}")
                    elif hasattr(symbol, "__name__"):
                        compile_wrapper.writeline(
                            f"from {symbol.__module__} import {symbol.__name__} as {symbol_name}"
                        )
                    symbols_included.add(symbol_name)