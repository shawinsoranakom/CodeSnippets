def discover_apis_from_xml(xml_dir: Path) -> dict[str, list[tuple[str, str]]]:
    """Parse Doxygen index.xml to discover all public APIs.

    Returns dict of category -> list of (symbol, kind).
    """
    index_path = xml_dir / "index.xml"
    if not index_path.exists():
        print(
            f"ERROR: {index_path} not found. Run 'make doxygen' first.",
            file=sys.stderr,
        )
        sys.exit(1)

    tree = ET.parse(index_path)
    root = tree.getroot()

    apis: dict[str, list[tuple[str, str]]] = {}

    # Collect classes and structs
    for compound in root.findall("compound"):
        kind = compound.get("kind")
        if kind not in ("class", "struct"):
            continue
        name = compound.find("name").text
        if _is_excluded(name):
            continue
        category = _categorize(name)
        apis.setdefault(category, []).append((name, kind))

    # Collect free functions from public namespaces
    for compound in root.findall("compound"):
        if compound.get("kind") != "namespace":
            continue
        ns_name = compound.find("name").text
        if ns_name not in PUBLIC_FUNCTION_NAMESPACES:
            continue
        seen_funcs = set()
        for member in compound.findall("member"):
            if member.get("kind") != "function":
                continue
            func_name = member.find("name").text
            qualified = f"{ns_name}::{func_name}"
            if qualified in seen_funcs:
                continue  # skip overloads
            seen_funcs.add(qualified)
            if _is_excluded(qualified):
                continue
            category = _categorize(qualified)
            apis.setdefault(category, []).append((qualified, "function"))

    # Collect macros (defines) from file compounds
    for compound in root.findall("compound"):
        if compound.get("kind") != "file":
            continue
        for member in compound.findall("member"):
            if member.get("kind") != "define":
                continue
            macro_name = member.find("name").text
            # Only track well-known public macros
            if macro_name.startswith(("TORCH_LIBRARY", "TORCH_MODULE")):
                if _is_excluded(macro_name):
                    continue
                apis.setdefault("torch (macros)", []).append((macro_name, "define"))

    # Sort each category and deduplicate
    for category in apis:
        apis[category] = sorted(set(apis[category]))

    return apis