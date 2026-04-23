def _capability_from_gcn_arch(gcn_arch: str) -> tuple[int, int] | None:
    """
    Parse (major, minor) from a GCN arch string, mirroring how
    HIP derives hipDeviceProp_t.major / .minor.

    Format: gfx<MAJOR><MINOR><STEPPING>
      - 1-digit major  (gfx9xx):  "gfx" + M + m + stepping
      - 2-digit major  (gfx1xxx): "gfx" + MM + m + stepping

    Examples:
      gfx90a  -> (9, 0)    gfx942  -> (9, 4)    gfx950 -> (9, 5)
      gfx1100 -> (11, 0)   gfx1101 -> (11, 0)   gfx1200 -> (12, 0)

    Returns None only when the string is not gfx-prefixed at all
    (i.e. not a ROCm arch string). Raises on any string that looks
    like a GCN arch but does not match a known layout.
    """
    m = re.match(r"gfx(\d+)", gcn_arch)
    if not m:
        # Not a gfx string at all — caller should fall back to torch.cuda
        return None

    digits = m.group(1)
    n = len(digits)

    if n < 2:
        raise ValueError(
            f"GCN arch '{gcn_arch}' has too few digits ({n}) after 'gfx' "
            f"to derive a (major, minor) capability. "
            f"Please file a vLLM issue with your GPU model."
        )

    if n in (2, 3):
        # 1-digit major: gfx9 family
        # len 2: major + minor          (e.g. gfx90 from gfx90a)
        # len 3: major + minor + step   (e.g. gfx942)
        major = int(digits[0])
        minor = int(digits[1])
    elif n == 4:
        # 2-digit major: gfx10xx, gfx11xx, gfx12xx
        # major(2) + minor(1) + stepping(1)
        major = int(digits[:2])
        minor = int(digits[2])
    elif n >= 5:
        raise ValueError(
            f"GCN arch '{gcn_arch}' has {n} digits after 'gfx', which "
            f"exceeds the known 4-digit layout (MMms). Cannot determine "
            f"major/minor split unambiguously. "
            f"Please file a vLLM issue with your GPU model."
        )

    if major < 9:
        raise ValueError(
            f"Parsed unknown ROCm architecture from GCN arch '{gcn_arch}': "
            f"major={major}, minor={minor}. "
            f"Major version < 9 is not expected for any supported AMD GPU. "
            f"Please file a vLLM issue with your GPU model."
        )

    if major > 12:
        raise ValueError(
            f"Parsed unknown ROCm architecture from GCN arch '{gcn_arch}': "
            f"major={major}, minor={minor}. "
            f"Major version > 12 is beyond currently known AMD generations. "
            f"Please file a vLLM issue with your GPU model so support "
            f"can be added."
        )

    return (major, minor)