def _ensure_utils_availability_imports(imports: list[cst.CSTNode], needed: set[str]) -> list[cst.CSTNode]:
    """Add is_torch_available and/or is_torchvision_available to the utils import if needed."""
    if not needed:
        return imports

    for i, node in enumerate(imports):
        if m.matches(node, m.SimpleStatementLine(body=[m.ImportFrom()])):
            import_from = node.body[0]
            if not isinstance(import_from, cst.ImportFrom) or import_from.module is None:
                continue
            module_str = import_from.module
            if isinstance(module_str, cst.Name):
                module_name = module_str.value
            elif isinstance(module_str, cst.Attribute):
                parts = []
                n = module_str
                while isinstance(n, cst.Attribute):
                    parts.append(n.attr.value)
                    n = n.value
                if isinstance(n, cst.Name):
                    parts.append(n.value)
                    module_name = ".".join(reversed(parts))
                else:
                    continue
            else:
                continue
            # Match ...utils or transformers.utils
            if not (module_name.endswith(".utils") or module_name == "utils"):
                continue
            existing = {a.name.value for a in import_from.names if isinstance(a.name, cst.Name)}
            to_add = [n for n in needed if n not in existing]
            if not to_add:
                continue
            new_names = list(import_from.names)
            for name in to_add:
                new_names.append(cst.ImportAlias(name=cst.Name(value=name)))
            new_import_from = import_from.with_changes(names=new_names)
            new_node = node.with_changes(body=[new_import_from])
            return imports[:i] + [new_node] + imports[i + 1 :]
    # No utils import found - add one (PIL files use ...utils for transformers.models.xxx)
    new_import = cst.parse_statement("from ...utils import " + ", ".join(sorted(needed)))
    return [new_import] + imports