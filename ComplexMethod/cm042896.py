def run_benchmark(config_name, custom_args=None, compare=True, clean=False):
    """Runs the stress test and optionally the report generator."""
    if config_name not in TEST_CONFIGS and config_name != "custom":
        console.print(f"[bold red]Unknown configuration: {config_name}[/bold red]")
        return False

    # Print header
    title = "Crawl4AI SDK Benchmark Test"
    if config_name != "custom":
        title += f" - {TEST_CONFIGS[config_name]['description']}"
    else:
        # Safely get custom args for title
        urls = custom_args.get('urls', '?') if custom_args else '?'
        sessions = custom_args.get('max_sessions', '?') if custom_args else '?'
        title += f" - Custom ({urls} URLs, {sessions} sessions)"

    console.print(f"\n[bold blue]{title}[/bold blue]")
    console.print("=" * (len(title) + 4)) # Adjust underline length

    console.print("\n[bold white]Preparing test...[/bold white]")

    # --- Command Construction ---
    # Use the new script name
    cmd = ["python", "test_stress_sdk.py"]

    # Apply config or custom args
    args_to_use = {}
    if config_name != "custom":
        args_to_use = TEST_CONFIGS[config_name].copy()
        # If custom args are provided (e.g., boolean flags), overlay them
        if custom_args:
            args_to_use.update(custom_args)
    elif custom_args: # Custom config
        args_to_use = custom_args.copy()

    # Add arguments with values
    for key, arg_name in FORWARD_ARGS.items():
        if key in args_to_use:
            cmd.extend([arg_name, str(args_to_use[key])])

    # Add boolean flags
    for key, flag_name in FORWARD_FLAGS.items():
        if args_to_use.get(key, False): # Check if key exists and is True
             # Special handling for clean flags - apply locally, don't forward?
             # Decide if test_stress_sdk.py also needs --clean flags or if run_benchmark handles it.
             # For now, let's assume run_benchmark handles cleaning based on its own --clean flag.
             # We'll forward other flags.
            if key not in ["clean_reports", "clean_site"]:
                 cmd.append(flag_name)

    # Handle the top-level --clean flag for run_benchmark
    if clean:
        # Pass clean flags to the stress test script as well, if needed
        # This assumes test_stress_sdk.py also uses --clean-reports and --clean-site
        cmd.append("--clean-reports")
        cmd.append("--clean-site")
        console.print("[yellow]Applying --clean: Cleaning reports and site before test.[/yellow]")
        # Actual cleaning logic might reside here or be delegated entirely

    console.print(f"\n[bold white]Running stress test:[/bold white] {' '.join(cmd)}")
    start = time.time()

    # Execute the stress test script
    # Use Popen to stream output
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            console.print(line.rstrip()) # Print line by line
        proc.wait() # Wait for the process to complete
    except FileNotFoundError:
         console.print(f"[bold red]Error: Script 'test_stress_sdk.py' not found. Make sure it's in the correct directory.[/bold red]")
         return False
    except Exception as e:
         console.print(f"[bold red]Error running stress test subprocess: {e}[/bold red]")
         return False


    if proc.returncode != 0:
        console.print(f"[bold red]Stress test failed with exit code {proc.returncode}[/bold red]")
        return False

    duration = time.time() - start
    console.print(f"[bold green]Stress test completed in {duration:.1f} seconds[/bold green]")

    # --- Report Generation (Optional) ---
    if compare:
        # Assuming benchmark_report.py exists and works with the generated reports
        report_script = "benchmark_report.py" # Keep configurable if needed
        report_cmd = ["python", report_script]
        console.print(f"\n[bold white]Generating benchmark report: {' '.join(report_cmd)}[/bold white]")

        # Run the report command and capture output
        try:
             report_proc = subprocess.run(report_cmd, capture_output=True, text=True, check=False, encoding='utf-8', errors='replace') # Use check=False to handle potential errors

             # Print the captured output from benchmark_report.py
             if report_proc.stdout:
                 console.print("\n" + report_proc.stdout)
             if report_proc.stderr:
                 console.print("[yellow]Report generator stderr:[/yellow]\n" + report_proc.stderr)

             if report_proc.returncode != 0:
                 console.print(f"[bold yellow]Benchmark report generation script '{report_script}' failed with exit code {report_proc.returncode}[/bold yellow]")
                 # Don't return False here, test itself succeeded
             else:
                  console.print(f"[bold green]Benchmark report script '{report_script}' completed.[/bold green]")

             # Find and print clickable links to the reports
             # Assuming reports are saved in 'benchmark_reports' by benchmark_report.py
             report_dir = "benchmark_reports"
             if os.path.isdir(report_dir):
                 report_files = glob.glob(os.path.join(report_dir, "comparison_report_*.html"))
                 if report_files:
                     try:
                         latest_report = max(report_files, key=os.path.getctime)
                         report_path = os.path.abspath(latest_report)
                         report_url = pathlib.Path(report_path).as_uri() # Better way to create file URI
                         console.print(f"[bold cyan]Click to open report: [link={report_url}]{report_url}[/link][/bold cyan]")
                     except Exception as e:
                          console.print(f"[yellow]Could not determine latest report: {e}[/yellow]")

                 chart_files = glob.glob(os.path.join(report_dir, "memory_chart_*.png"))
                 if chart_files:
                      try:
                         latest_chart = max(chart_files, key=os.path.getctime)
                         chart_path = os.path.abspath(latest_chart)
                         chart_url = pathlib.Path(chart_path).as_uri()
                         console.print(f"[cyan]Memory chart: [link={chart_url}]{chart_url}[/link][/cyan]")
                      except Exception as e:
                           console.print(f"[yellow]Could not determine latest chart: {e}[/yellow]")
             else:
                  console.print(f"[yellow]Benchmark report directory '{report_dir}' not found. Cannot link reports.[/yellow]")

        except FileNotFoundError:
             console.print(f"[bold red]Error: Report script '{report_script}' not found.[/bold red]")
        except Exception as e:
             console.print(f"[bold red]Error running report generation subprocess: {e}[/bold red]")


    # Prompt to exit
    console.print("\n[bold green]Benchmark run finished. Press Enter to exit.[/bold green]")
    try:
        input() # Wait for user input
    except EOFError:
        pass # Handle case where input is piped or unavailable

    return True