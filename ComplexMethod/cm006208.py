def run_command(cmd, check=True, capture_output=False):
    """Run a shell command with proper error handling."""
    print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True, check=check)
            return result.stdout.strip()
        subprocess.run(cmd, shell=isinstance(cmd, str), check=check)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        if capture_output and e.stdout:
            print(f"STDOUT: {e.stdout}")
        if capture_output and e.stderr:
            print(f"STDERR: {e.stderr}")
        if check:
            sys.exit(1)