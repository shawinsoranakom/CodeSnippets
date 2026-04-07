def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()