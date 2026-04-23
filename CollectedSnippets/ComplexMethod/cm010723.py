def find_triton_kernels(
        fn: Callable[..., Any],
        visited_fns: set[int] | None = None,
        depth: int = 0,
    ) -> list[object]:
        try:
            from triton.runtime.autotuner import Autotuner
            from triton.runtime.jit import JITFunction
        except ImportError:
            logger.warning("Triton not available, find_triton_kernels = []")
            return []

        # unwrap decorated fn's (e.g., @lru_cache) to get the original
        fn = inspect.unwrap(fn)

        # init visited set and check for cycles/depth limit
        if visited_fns is None:
            visited_fns = set()

        fn_id = id(fn)
        if fn_id in visited_fns:
            return []
        if depth > MAX_RECURSION_DEPTH:
            logger.debug(
                "reached max recursion depth (%s) in find_triton_kernels",
                MAX_RECURSION_DEPTH,
            )
            return []

        visited_fns.add(fn_id)

        try:
            source = inspect.getsource(fn)
        except (OSError, TypeError):
            return []  # Source code not available

        from torch._inductor.utils import IndentedBuffer

        buffer = IndentedBuffer()
        buffer.splice(source, strip=True)
        tree = ast.parse(buffer.getrawvalue())

        # Visitor to collect function calls, assignments, and triton kernels
        class Visitor(ast.NodeVisitor):
            def __init__(self) -> None:
                self.triton_kernels: list[Any] = []
                # track local variable assignments: var_name -> list of RHS expressions
                self.assignments: dict[str, list[ast.expr]] = {}
                # track function calls
                self.called_functions: list[str] = []
                # track return statement expressions
                self.return_exprs: list[ast.expr] = []

            def visit_Assign(self, node: ast.Assign) -> None:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.assignments.setdefault(target.id, []).append(node.value)
                self.generic_visit(node)

            def visit_Return(self, node: ast.Return) -> None:
                if node.value is not None:
                    self.return_exprs.append(node.value)
                self.generic_visit(node)

            def visit_Call(self, node: ast.Call) -> None:
                triton_func_names = ("capture_triton", "wrap_triton")
                if isinstance(node.func, ast.Attribute):
                    attr = node.func
                    if isinstance(attr.value, ast.Attribute):
                        if (
                            isinstance(attr.value.value, ast.Name)
                            and attr.value.value.id == "torch"
                            and attr.value.attr == "_library"
                            and attr.attr in triton_func_names
                        ):
                            if node.args and isinstance(node.args[0], ast.Name):
                                self.triton_kernels.append(node.args[0].id)
                        elif (
                            isinstance(attr.value.value, ast.Attribute)
                            and isinstance(attr.value.value.value, ast.Name)
                            and attr.value.value.value.id == "torch"
                            and attr.value.value.attr == "ops"
                        ):
                            self.called_functions.append(
                                f"{attr.value.attr}::{attr.attr}"
                            )
                # Catch capture_triton, wrap_triton that's been
                # imported directly
                elif isinstance(node.func, ast.Name):
                    if node.func.id in triton_func_names:
                        if node.args and isinstance(node.args[0], ast.Name):
                            self.triton_kernels.append(node.args[0].id)
                    else:
                        # track regular function calls for recursive analysis
                        self.called_functions.append(node.func.id)

                self.generic_visit(node)

        collector = Visitor()
        collector.visit(tree)

        def extract_names_from_expr(expr: ast.expr) -> list[str]:
            """Extract all Name references from an AST expression."""
            names: list[str] = []

            class NameExtractor(ast.NodeVisitor):
                def visit_Name(self, node: ast.Name) -> None:
                    names.append(node.id)

                def visit_Call(self, node: ast.Call) -> None:
                    # for function calls, visit the function and all args
                    self.generic_visit(node)

            NameExtractor().visit(expr)
            return names

        def resolve_to_kernel(obj: object) -> object | None:
            """Check if obj is a triton kernel or wrapper and return the kernel."""
            if isinstance(obj, (JITFunction, Autotuner)):
                return obj
            # handle wrappers that have a .fn attribute pointing to JITFunction
            if callable(obj) and hasattr(obj, "fn"):
                inner = obj.fn
                if isinstance(inner, JITFunction):
                    return inner
            return None

        def build_namespace(func_obj: object) -> dict[str, Any]:
            """Build a combined namespace from a function's globals and closures."""
            # unwrap decorated fns (e.g., @lru_cache)
            if callable(func_obj):
                try:
                    func_obj = inspect.unwrap(func_obj)
                except ValueError:
                    pass
            if not callable(func_obj) or not hasattr(func_obj, "__code__"):
                return {}
            func_closure_vars = inspect.getclosurevars(func_obj)
            namespace: dict[str, Any] = {}
            namespace.update(func_closure_vars.builtins)
            namespace.update(func_closure_vars.globals)
            namespace.update(func_closure_vars.nonlocals)
            if hasattr(func_obj, "__globals__"):
                namespace.update(func_obj.__globals__)
            return namespace

        all_names = build_namespace(fn)

        def resolve_names_to_kernels(
            names: list[str],
            namespace: dict[str, Any],
            assignments: dict[str, list[ast.expr]] | None = None,
            visited: set[str] | None = None,
        ) -> list[object]:
            """
            Resolve a list of names to triton kernels using the given namespace.
            """
            if visited is None:
                visited = set()

            results: list[object] = []
            for name in names:
                if name in visited:
                    continue
                visited.add(name)

                if name in namespace:
                    obj = namespace[name]
                    kernel = resolve_to_kernel(obj)
                    if kernel is not None:
                        results.append(kernel)
                        continue
                    # recurse into callable objects (factory fn's),
                    # unwrapping decorators if applicable
                    if callable(obj):
                        try:
                            unwrapped = inspect.unwrap(obj)
                        except ValueError:
                            unwrapped = obj
                        if hasattr(unwrapped, "__code__"):
                            nested = find_triton_kernels(
                                unwrapped, visited_fns, depth + 1
                            )
                            if nested:
                                results.extend(nested)
                                continue
                    logger.debug("failed to resolve %s to a triton kernel", name)
                elif assignments is not None and name in assignments:
                    # trace through local assignments
                    for rhs_expr in assignments[name]:
                        referenced = extract_names_from_expr(rhs_expr)
                        traced = resolve_names_to_kernels(
                            referenced, namespace, assignments, visited
                        )
                        results.extend(traced)
                else:
                    logger.debug("%s not found in namespace or assignments", name)

            return results

        # resolve kernel names, tracing through local variables if needed
        resolved: list[object] = []
        seen_ids: set[int] = set()

        names_to_resolve: list[str] = list(collector.triton_kernels)
        for expr in collector.return_exprs:
            names_to_resolve.extend(extract_names_from_expr(expr))

        for name in names_to_resolve:
            traced_objects = resolve_names_to_kernels(
                [name], all_names, collector.assignments
            )
            for obj in traced_objects:
                obj_id = id(obj)
                if obj_id not in seen_ids:
                    seen_ids.add(obj_id)
                    resolved.append(obj)

        for func_name in collector.called_functions:
            func_obj = all_names.get(func_name)

            if func_obj is None:
                from torch._library.custom_ops import OPDEFS

                if func_name in OPDEFS:
                    func_obj = OPDEFS[func_name]._abstract_fn

            # skip if not a callable or if it's a triton kernel itself
            if func_obj is None or not callable(func_obj):
                continue

            # skip built-in functions and C extensions (they can't contain triton kernels)
            if not hasattr(func_obj, "__code__"):
                continue

            try:
                nested_kernels = find_triton_kernels(func_obj, visited_fns, depth + 1)
                for kernel in nested_kernels:
                    kernel_id = id(kernel)
                    if kernel_id not in seen_ids:
                        seen_ids.add(kernel_id)
                        resolved.append(kernel)
            except Exception:
                logger.debug(
                    "failed to analyze called function %s", func_name, exc_info=True
                )

        return resolved