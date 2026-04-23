def main():
    parser = argparse.ArgumentParser(description="Run check/fix scripts.")
    parser.add_argument(
        "checkers",
        nargs="+",
        help='Comma-separated checker names, or "all". Use --list to see available checkers.',
    )
    parser.add_argument("--fix", action="store_true", help="Run in fix mode instead of check mode.")
    parser.add_argument(
        "--keep-going", action="store_true", help="Run all checkers even if some fail (report failures at the end)."
    )
    parser.add_argument("--list", action="store_true", help="List available checkers and exit.")
    parser.add_argument("--no-cache", action="store_true", help="Ignore the disk cache and re-run every checker.")

    args = parser.parse_args()

    if args.list:
        for name, entry in sorted(CHECKERS.items()):
            label, script, _, fix_args = entry
            fixable = "fixable" if fix_args is not None else "check-only"
            script_display = script or "custom"
            print(f"  {name:25s} {label:35s} ({script_display}, {fixable})")
        return

    # Join all positional args (shell line continuations may split them) and parse checker names
    raw = " ".join(args.checkers)
    if raw.strip() == "all":
        names = list(CHECKERS.keys())
    else:
        names = [n.strip() for n in raw.split(",") if n.strip()]

    unknown = [n for n in names if n not in CHECKERS]
    if unknown:
        print(f"Unknown checkers: {', '.join(unknown)}")
        print(f"Available: {', '.join(sorted(CHECKERS.keys()))}")
        sys.exit(1)

    is_ci = os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("CIRCLECI") == "true"
    is_tty = sys.stdout.isatty() and not is_ci

    if not is_tty and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)

    use_cache = not args.no_cache and not args.fix
    cache = CheckerCache() if use_cache else None

    failures = []
    skipped = 0
    total_start = time.perf_counter()
    for name in names:
        label = CHECKERS[name][0]

        # Skip if all relevant files are unchanged since last clean run
        if cache is not None and cache.is_current(name):
            skipped += 1
            if is_tty:
                print(f"{GREEN}✓ {label} (cached){RESET}\n")
            else:
                print(f"{label} (cached)\n", flush=True)
            continue

        cmd_str = get_checker_command(name, fix=args.fix)
        checker_start = time.perf_counter()

        if is_tty:
            window = SlidingWindow(label, max_lines=10)
            if cmd_str:
                window.add_line(f"$ {cmd_str}")
            rc, output = run_checker(name, fix=args.fix, line_callback=window.add_line)
            elapsed = time.perf_counter() - checker_start
            window.finish(success=(rc == 0), elapsed=elapsed, show_lines=(rc == 0))
            if rc != 0:
                print()
                _print_output(output)
            print()
            if rc == 0 and cache is not None:
                cache.update(name)
            elif rc != 0:
                if cache is not None:
                    cache.invalidate(name)
                failures.append(name)
                if not args.keep_going:
                    if cache is not None:
                        cache.save()
                    sys.exit(1)
        else:
            print(f"{label}", flush=True)
            if cmd_str:
                print(f"$ {cmd_str}", flush=True)
            if is_ci:
                streamed_output = []

                def print_line(line):
                    streamed_output.append(line)
                    print(line, end="", flush=True)

                rc, output = run_checker(name, fix=args.fix, line_callback=print_line)
                if rc != 0 and output:
                    streamed_text = "".join(streamed_output)
                    if output.startswith(streamed_text):
                        _print_output(output[len(streamed_text) :])
                    elif output != streamed_text:
                        _print_output(output)
            else:
                rc, output = run_checker(name, fix=args.fix)
                if rc == 0:
                    tail = output.splitlines()[-10:]
                    if tail:
                        print("\n".join(tail), flush=True)
                else:
                    _print_output(output)
            elapsed = time.perf_counter() - checker_start
            status = "OK" if rc == 0 else "FAILED"
            print(f"{status} ({format_elapsed(elapsed)})", flush=True)
            print(flush=True)
            if rc == 0 and cache is not None:
                cache.update(name)
            elif rc != 0:
                if cache is not None:
                    cache.invalidate(name)
                failures.append(name)
                if not args.keep_going:
                    if cache is not None:
                        cache.save()
                    sys.exit(1)

    if cache is not None:
        cache.save()

    if failures:
        print(f"\n{len(failures)} failed: {', '.join(failures)}", flush=True)
        sys.exit(1)

    total_elapsed = format_elapsed(time.perf_counter() - total_start)
    passed = len(names) - skipped
    if skipped:
        print(f"\nAll {len(names)} checks passed in {total_elapsed} ({passed} ran, {skipped} cached).", flush=True)
    else:
        print(f"\nAll {len(names)} checks passed in {total_elapsed}.", flush=True)