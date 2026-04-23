def run_fuzzer_with_seed(
    seed: int,
    template: str = "default",
    supported_ops: str | None = None,
) -> FuzzerResult:
    """
    Run fuzzer.py with a specific seed.

    Args:
        seed: The seed value to pass to fuzzer.py
        template: The template to use for code generation
        supported_ops: Comma-separated ops string with optional weights

    Returns:
        FuzzerResult dataclass instance
    """
    start_time = time.time()

    try:
        # Run fuzzer.py with the specified seed and template
        cmd = [
            sys.executable,
            "fuzzer.py",
            "--single",
            "--seed",
            str(seed),
            "--template",
            template,
        ]

        # Append supported ops if provided
        if supported_ops:
            cmd.extend(["--supported-ops", supported_ops])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout per seed
        )

        duration = time.time() - start_time
        success = result.returncode == 0

        # Combine stdout and stderr for output
        output = ""
        if result.stdout:
            output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"STDERR:\n{result.stderr}\n"
        output += f"Return code: {result.returncode}"

        # Parse operation statistics from the output
        operation_stats = {}
        if result.stdout:
            lines = result.stdout.split("\n")
            in_stats_section = False
            for line in lines:
                if line.strip() == "OPERATION_STATS:":
                    in_stats_section = True
                    continue
                elif in_stats_section:
                    if line.startswith("  ") and ":" in line:
                        # Parse line like "  torch.add: 3"
                        op_line = line.strip()
                        if ": " in op_line:
                            op_name, count_str = op_line.split(": ", 1)
                            try:
                                count = int(count_str)
                                operation_stats[op_name] = count
                            except ValueError:
                                pass  # Skip malformed lines
                    else:
                        # End of stats section
                        in_stats_section = False

        # Check if output should be ignored and which pattern matched
        ignored_pattern_idx = is_ignored_output(output)
        if ignored_pattern_idx != -1:
            # Mark as ignored (could also return a special flag if needed)
            output = "[IGNORED] " + output

        return FuzzerResult(
            seed, success, output, duration, ignored_pattern_idx, operation_stats
        )

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        return FuzzerResult(
            seed, False, "Process timed out after 300 seconds", duration, -1, {}
        )

    except Exception as e:
        duration = time.time() - start_time
        return FuzzerResult(
            seed, False, f"Exception occurred: {str(e)}", duration, -1, {}
        )