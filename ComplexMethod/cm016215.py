def run_fuzzer_with_seed(seed):
    """Run the fuzzer with a specific seed and return the generated code."""
    cmd = [sys.executable, "fuzzer.py", "--seed", str(seed), "--template", "unbacked"]

    # Clear the output directory first
    torchfuzz_dir = Path("/tmp/torchfuzz")
    if torchfuzz_dir.exists():
        for f in torchfuzz_dir.glob("*.py"):
            f.unlink()

    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=Path(__file__).parent
    )

    # Always attempt to read the generated file even if execution failed.
    if result.returncode != 0:
        print(f"Fuzzer failed with return code {result.returncode}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")

    # Prefer to compare the exact Program Source that the fuzzer printed in stdout,
    # which reflects the executed code even if files are overwritten between runs.
    src_block = None
    lines = result.stdout.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "=== Program Source ===":
            # Collect until the next delimiter line of === or the end
            j = i + 1
            block_lines = []
            while j < len(lines) and not lines[j].startswith("==="):
                block_lines.append(lines[j])
                j += 1
            src_block = "\n".join(block_lines)
            break

    if src_block:
        return src_block

    # Fallback: parse the exact path the fuzzer ran from stdout: "Running: /tmp/torchfuzz/fuzz_XXXX.py"
    path = None
    for line in lines:
        if line.startswith("Running: ") and line.strip().endswith(".py"):
            path = line.split("Running: ", 1)[1].strip()
            break

    if path is None:
        # Fallback: pick the most recently modified fuzz_*.py in /tmp/torchfuzz
        py_files = sorted(
            torchfuzz_dir.glob("fuzz_*.py"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not py_files:
            print("No Python files generated in /tmp/torchfuzz/")
            return None
        path = str(py_files[0])

    # Read the content of the generated file that was actually executed
    with open(path) as f:
        return f.read()