def start(agent_name: str, no_setup: bool):
    """Start agent command"""
    import os
    import subprocess

    script_dir = os.path.dirname(os.path.realpath(__file__))
    agent_dir = os.path.join(
        script_dir,
        f"agents/{agent_name}"
        if agent_name not in ["original_autogpt", "forge"]
        else agent_name,
    )
    run_command = os.path.join(agent_dir, "run")
    run_bench_command = os.path.join(agent_dir, "run_benchmark")
    if (
        os.path.exists(agent_dir)
        and os.path.isfile(run_command)
        and os.path.isfile(run_bench_command)
    ):
        os.chdir(agent_dir)
        if not no_setup:
            click.echo(f"⌛ Running setup for agent '{agent_name}'...")
            setup_process = subprocess.Popen(["./setup"], cwd=agent_dir)
            setup_process.wait()
            click.echo()

        # FIXME: Doesn't work: Command not found: agbenchmark
        # subprocess.Popen(["./run_benchmark", "serve"], cwd=agent_dir)
        # click.echo("⌛ (Re)starting benchmark server...")
        # wait_until_conn_ready(8080)
        # click.echo()

        subprocess.Popen(["./run"], cwd=agent_dir)
        click.echo(f"⌛ (Re)starting agent '{agent_name}'...")
        wait_until_conn_ready(8000)
        click.echo("✅ Agent application started and available on port 8000")
    elif not os.path.exists(agent_dir):
        click.echo(
            click.style(
                f"😞 Agent '{agent_name}' does not exist. Please create the agent first.",
                fg="red",
            )
        )
    else:
        click.echo(
            click.style(
                f"😞 Run command does not exist in the agent '{agent_name}' directory.",
                fg="red",
            )
        )
