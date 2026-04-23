def find_latest_pwsh_sdk_path(
    executable_name='pwsh.exe',
    dll_name='System.Management.Automation.dll',
    min_version=(7, 0, 0),
    env_var='PWSH_DIR',
):
    """
    Checks PWSH_DIR environment variable first to find pwsh and DLL.
    If not found or not suitable, scans all pwsh executables in PATH, runs --version to find latest >= min_version.
    Returns full DLL path if found, else None.
    """

    def parse_version(output):
        # Extract semantic version from pwsh --version output
        match = re.search(r'(\d+)\.(\d+)\.(\d+)', output)
        if match:
            return tuple(map(int, match.groups()))
        return None

    # Try environment variable override first
    pwsh_dir = os.environ.get(env_var)
    if pwsh_dir:
        pwsh_path = Path(pwsh_dir) / executable_name
        dll_path = Path(pwsh_dir) / dll_name
        if pwsh_path.is_file() and dll_path.is_file():
            try:
                completed = subprocess.run(
                    [str(pwsh_path), '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if completed.returncode == 0:
                    ver = parse_version(completed.stdout)
                    if ver and ver >= min_version:
                        logger.info(f'Found pwsh from env variable "{env_var}"')
                        return str(dll_path)
            except Exception:
                pass

    # Adjust executable_name for Windows if needed
    if os.name == 'nt' and not executable_name.lower().endswith('.exe'):
        executable_name += '.exe'

    # Search PATH for all pwsh executables
    paths = os.environ.get('PATH', '').split(os.pathsep)
    candidates = []
    for p in paths:
        exe_path = Path(p) / executable_name
        if exe_path.is_file() and os.access(str(exe_path), os.X_OK):
            try:
                completed = subprocess.run(
                    [str(exe_path), '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if completed.returncode == 0:
                    ver = parse_version(completed.stdout)
                    if ver:
                        candidates.append((ver, exe_path.resolve()))
            except Exception:
                pass

    # Sort candidates by version descending
    candidates.sort(key=lambda x: x[0], reverse=True)

    for ver, exe_path in candidates:
        if ver >= min_version:
            dll_path = exe_path.parent / dll_name
            if dll_path.is_file():
                return str(dll_path)

    return None