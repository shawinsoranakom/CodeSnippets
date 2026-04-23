def run_coverxygen(xml_dir: Path) -> str:
    """Run coverxygen on Doxygen XML output for doc-comment coverage."""
    lines = []
    lines.append("Coverxygen Report (Doxygen doc-comment coverage)")
    lines.append("=" * 50)
    lines.append("")

    if not xml_dir.exists():
        lines.append("ERROR: build/xml directory not found. Run 'make doxygen' first.")
        return "\n".join(lines)

    coverxygen_cmd = None
    for cmd in [
        ["coverxygen", "--version"],
        [sys.executable, "-m", "coverxygen", "--version"],
    ]:
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            coverxygen_cmd = cmd[:-1]
            break
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    if coverxygen_cmd is None:
        lines.append("coverxygen not installed. Install with: pip install coverxygen")
        lines.append("")
        lines.append("Once installed, coverxygen analyzes Doxygen XML to report what")
        lines.append("percentage of C++ symbols have doc comments in the source code.")
        lines.append("This is complementary to the RST coverage check above.")
        lines.append("")
        lines.append("Usage:")
        lines.append(
            f"  coverxygen --xml-dir {xml_dir} --src-dir ../../ --output coverxygen.info"
        )
        lines.append("  # Then use lcov/genhtml to visualize:")
        lines.append(
            "  genhtml --no-function-coverage coverxygen.info -o coverxygen_html"
        )
        return "\n".join(lines)

    try:
        result = subprocess.run(
            coverxygen_cmd
            + [
                "--xml-dir",
                str(xml_dir),
                "--src-dir",
                str(SCRIPT_DIR / ".." / ".."),
                "--output",
                "-",
                "--kind",
                "class,struct,function",
                "--scope",
                "public",
                "--exclude",
                ".*/build/.*",
                "--exclude",
                ".*/detail/.*",
                "--exclude",
                ".*/nativert/.*",
                "--exclude",
                ".*/stable/library\\.h",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            total = 0
            documented_count = 0
            for line in result.stdout.splitlines():
                if line.startswith("DA:"):
                    total += 1
                    parts = line.split(",")
                    if len(parts) >= 2 and parts[1].strip() != "0":
                        documented_count += 1
            pct = (documented_count / total * 100) if total else 0
            lines.append(f"Symbols scanned:    {total}")
            lines.append(f"With doc comments:  {documented_count}")
            lines.append(f"Coverage:           {pct:.1f}%")
            lines.append("")
            lines.append("Full lcov output saved to: coverxygen.info")
            (SCRIPT_DIR / "coverxygen.info").write_text(result.stdout)
        else:
            lines.append(f"coverxygen failed (exit {result.returncode}):")
            lines.append(result.stderr[:500])
    except subprocess.TimeoutExpired:
        lines.append("coverxygen timed out after 120s")
    except Exception as e:
        lines.append(f"coverxygen error: {e}")

    lines.append("")
    return "\n".join(lines)