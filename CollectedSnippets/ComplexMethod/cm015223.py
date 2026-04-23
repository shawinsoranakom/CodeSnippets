def filter_vmap_implementable(reg):
    reg = reg.lower()
    if not reg.startswith("aten::"):
        return False
    if reg.startswith("aten::_"):
        return False
    if reg.endswith(".out"):
        return False
    if reg.endswith("_out"):
        return False
    if ".dimname" in reg:
        return False
    if "_dimname" in reg:
        return False
    if "fbgemm" in reg:
        return False
    if "quantize" in reg:
        return False
    if "sparse" in reg:
        return False
    if "::is_" in reg:
        return False
    return True