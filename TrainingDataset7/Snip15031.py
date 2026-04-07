def run(cmd, *, cwd=None, env=None, dry_run=True):
    """Run a command with optional dry-run behavior."""
    environ = os.environ.copy()
    if env:
        environ.update(env)
    if dry_run:
        print("[DRY RUN]", " ".join(cmd))
    else:
        print("[EXECUTE]", " ".join(cmd))
        try:
            result = subprocess.check_output(
                cmd, cwd=cwd, env=environ, stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as e:
            result = e.output
            print("    [ERROR]", result)
            raise
        else:
            print("    [RESULT]", result)
        return result.decode().strip()