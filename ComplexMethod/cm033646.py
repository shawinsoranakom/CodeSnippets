def detect_architecture(python: str) -> t.Optional[str]:
    """Detect the architecture of the specified Python and return a normalized version, or None if it cannot be determined."""
    results: dict[str, t.Optional[str]]

    try:
        results = detect_architecture.results  # type: ignore[attr-defined]
    except AttributeError:
        results = detect_architecture.results = {}  # type: ignore[attr-defined]

    if python in results:
        return results[python]

    if python == sys.executable or os.path.realpath(python) == os.path.realpath(sys.executable):
        uname = platform.uname()
    else:
        data = raw_command([python, '-c', 'import json, platform; print(json.dumps(platform.uname()));'], capture=True)[0]
        uname = json.loads(data)

    translation = {
        'x86_64': Architecture.X86_64,  # Linux, macOS
        'amd64': Architecture.X86_64,  # FreeBSD
        'aarch64': Architecture.AARCH64,  # Linux, FreeBSD
        'arm64': Architecture.AARCH64,  # FreeBSD
    }

    candidates = []

    if len(uname) >= 5:
        candidates.append(uname[4])

    if len(uname) >= 6:
        candidates.append(uname[5])

    candidates = sorted(set(candidates))
    architectures = sorted(set(arch for arch in [translation.get(candidate) for candidate in candidates] if arch))

    architecture: t.Optional[str] = None

    if not architectures:
        display.warning(f'Unable to determine architecture for Python interpreter "{python}" from: {candidates}')
    elif len(architectures) == 1:
        architecture = architectures[0]
        display.info(f'Detected architecture {architecture} for Python interpreter: {python}', verbosity=1)
    else:
        display.warning(f'Conflicting architectures detected ({architectures}) for Python interpreter "{python}" from: {candidates}')

    results[python] = architecture

    return architecture