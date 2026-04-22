def run_component_template_e2e_test(ctx: Context, template_dir: str, name: str) -> bool:
    """Build a component template and run its e2e tests."""
    frontend_dir = join(template_dir, "frontend")

    # Install the template's npm dependencies into its node_modules.
    subprocess.run(
        ["yarn", "install"],
        cwd=frontend_dir,
        capture_output=True,
        text=True,
        check=True,
    )

    # Start the template's dev server.
    with AsyncSubprocess(["yarn", "start"], cwd=frontend_dir) as webpack_proc:
        # Run the test!
        main_script_path = join(template_dir, "__init__.py")
        spec_path = join(ROOT_DIR, "e2e/specs/component_template.spec.js")

        ctx.cypress_env_vars["COMPONENT_TEMPLATE_TYPE"] = name
        success = run_test(ctx, spec_path, ["streamlit", "run", main_script_path])
        del ctx.cypress_env_vars["COMPONENT_TEMPLATE_TYPE"]

        webpack_stdout = webpack_proc.terminate()

    if not success:
        click.echo(
            f"{click.style('webpack output:', fg='yellow', bold=True)}"
            f"\n{webpack_stdout}"
            f"\n"
        )

    return success