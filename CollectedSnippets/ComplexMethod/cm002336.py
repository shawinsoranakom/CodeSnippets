def protect_torch_imports_for_pil(imports: list[cst.CSTNode]) -> list[cst.CSTNode]:
    """
    For PIL image processor files, collect all torch/torchvision imports — whether bare or
    already wrapped in a guard — into a single `if is_torch_available():` /
    `if is_torchvision_available():` block each. Add the required availability checks to the
    utils import.

    Pre-existing guarded blocks (no else clause) are absorbed so we never emit duplicate guards
    for the same library.
    """
    torch_stmts: list[cst.CSTNode] = []
    torchvision_stmts: list[cst.CSTNode] = []
    other_imports: list[cst.CSTNode] = []
    torch_needed: set[str] = set()
    torchvision_needed: set[str] = set()

    def _code(node: cst.CSTNode) -> str:
        return cst.Module(body=[node]).code.strip()

    for node in imports:
        if m.matches(node, m.If()):
            # Absorb simple torch/torchvision guards (no else) to merge into one combined block.
            node_code = _code(node)
            if "is_torch_available()" in node_code and node.orelse is None:
                torch_stmts.extend(node.body.body)
                torch_needed.add("is_torch_available")
            elif "is_torchvision_available()" in node_code and node.orelse is None:
                torchvision_stmts.extend(node.body.body)
                torchvision_needed.add("is_torchvision_available")
            else:
                other_imports.append(node)
        elif m.matches(node, m.SimpleStatementLine(body=[m.Import() | m.ImportFrom()])):
            node_code = _code(node)
            # Check torchvision before torch — "torchvision" starts with "torch"
            if node_code.startswith("import torchvision") or node_code.startswith("from torchvision"):
                torchvision_stmts.append(node)
                torchvision_needed.add("is_torchvision_available")
            elif node_code.startswith("import torch") or node_code.startswith("from torch"):
                torch_stmts.append(node)
                torch_needed.add("is_torch_available")
            else:
                other_imports.append(node)
        else:
            other_imports.append(node)

    result: list[cst.CSTNode] = []
    if torch_stmts:
        body = "\n    ".join(_code(s) for s in torch_stmts)
        result.append(cst.parse_statement(f"if is_torch_available():\n    {body}"))
    if torchvision_stmts:
        body = "\n    ".join(_code(s) for s in torchvision_stmts)
        result.append(cst.parse_statement(f"if is_torchvision_available():\n    {body}"))

    if availability_needed := torch_needed | torchvision_needed:
        other_imports = _ensure_utils_availability_imports(other_imports, availability_needed)

    # Protected imports at the end (after usual_import_nodes in get_needed_imports order)
    return other_imports + result