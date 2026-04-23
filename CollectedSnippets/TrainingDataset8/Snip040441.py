def run_e2e_tests(
    always_continue: bool,
    record_results: bool,
    update_snapshots: bool,
    flaky_tests: bool,
    tests: List[str],
    verbose: bool,
):
    """Run e2e tests. If any fail, exit with non-zero status."""
    kill_streamlits()
    kill_app_servers()
    app_server = run_app_server()

    # Clear reports from previous runs
    remove_if_exists("frontend/test_results/cypress")

    ctx = Context()
    ctx.always_continue = always_continue
    ctx.record_results = record_results
    ctx.update_snapshots = update_snapshots
    ctx.tests_dir_name = "e2e_flaky" if flaky_tests else "e2e"

    try:
        p = Path(join(ROOT_DIR, ctx.tests_dir_name, "specs")).resolve()
        if tests:
            paths = [Path(t).resolve() for t in tests]
        else:
            paths = sorted(p.glob("*.spec.js"))
        for spec_path in paths:
            if basename(spec_path) == "st_hello.spec.js":
                if flaky_tests:
                    continue

                # Test "streamlit hello" in both headless and non-headless mode.
                run_test(
                    ctx,
                    str(spec_path),
                    ["streamlit", "hello", "--server.headless=false"],
                    show_output=verbose,
                )
                run_test(
                    ctx,
                    str(spec_path),
                    ["streamlit", "hello", "--server.headless=true"],
                    show_output=verbose,
                )

            elif basename(spec_path) == "component_template.spec.js":
                if flaky_tests:
                    continue
                for name, template_dir in COMPONENT_TEMPLATE_DIRS.items():
                    run_component_template_e2e_test(ctx, template_dir, name)

            elif basename(spec_path) == "multipage_apps.spec.js":
                test_name, _ = splitext(basename(spec_path))
                test_name, _ = splitext(test_name)
                test_path = join(
                    ctx.tests_dir, "scripts", "multipage_apps", "streamlit_app.py"
                )
                if os.path.exists(test_path):
                    run_test(
                        ctx,
                        str(spec_path),
                        ["streamlit", "run", "--ui.hideSidebarNav=false", test_path],
                        show_output=verbose,
                    )

            else:
                test_name, _ = splitext(basename(spec_path))
                test_name, _ = splitext(test_name)
                test_path = join(ctx.tests_dir, "scripts", f"{test_name}.py")
                if os.path.exists(test_path):
                    run_test(
                        ctx,
                        str(spec_path),
                        ["streamlit", "run", test_path],
                        show_output=verbose,
                    )
    except QuitException:
        # Swallow the exception we raise if the user chooses to exit early.
        pass
    finally:
        if app_server:
            app_server.terminate()

    if ctx.any_failed:
        sys.exit(1)