def _parse_vllm_env_txt(env_path: Path) -> pd.DataFrame:
    """Parse vllm_env.txt into a flat table (Section, Key, Value).

    Supports:
      - section headers as standalone lines (no ':' or '=')
      - key-value lines like 'OS: Ubuntu ...'
      - env var lines like 'HF_HOME=/data/hf'
    """
    lines = env_path.read_text(encoding="utf-8", errors="replace").splitlines()
    section = "General"
    rows: list[dict] = []

    def set_section(s: str):
        nonlocal section
        s = (s or "").strip()
        if s:
            section = s

    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue
        # divider lines like =====
        if set(stripped) <= {"="}:
            continue

        # section header heuristic: short standalone line
        if ":" not in stripped and "=" not in stripped and len(stripped) <= 64:
            if stripped.lower().startswith("collecting environment information"):
                continue
            set_section(stripped)
            continue

        # env var style: KEY=VALUE (and not a URL with :)
        if "=" in stripped and ":" not in stripped:
            k, v = stripped.split("=", 1)
            k = k.strip()
            v = v.strip()
            if k:
                rows.append({"Section": section, "Key": k, "Value": v})
            continue

        # key: value
        if ":" in stripped:
            k, v = stripped.split(":", 1)
            k = k.strip()
            v = v.strip()
            if k:
                rows.append({"Section": section, "Key": k, "Value": v})
            continue

    return pd.DataFrame(rows, columns=["Section", "Key", "Value"])