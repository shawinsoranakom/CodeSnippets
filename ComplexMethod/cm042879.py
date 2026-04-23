def get_declared_dependencies() -> Set[str]:
    """Get declared dependencies from pyproject.toml and requirements.txt"""
    declared = set()

    # Read from pyproject.toml
    if Path('pyproject.toml').exists():
        with open('pyproject.toml', 'r') as f:
            data = toml.load(f)

        # Get main dependencies
        deps = data.get('project', {}).get('dependencies', [])
        for dep in deps:
            # Parse dependency string (e.g., "numpy>=1.26.0,<3")
            match = re.match(r'^([a-zA-Z0-9_-]+)', dep)
            if match:
                pkg_name = match.group(1).lower()
                declared.add(pkg_name)

        # Get optional dependencies
        optional = data.get('project', {}).get('optional-dependencies', {})
        for group, deps in optional.items():
            for dep in deps:
                match = re.match(r'^([a-zA-Z0-9_-]+)', dep)
                if match:
                    pkg_name = match.group(1).lower()
                    declared.add(pkg_name)

    # Also check requirements.txt as backup
    if Path('requirements.txt').exists():
        with open('requirements.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    match = re.match(r'^([a-zA-Z0-9_-]+)', line)
                    if match:
                        pkg_name = match.group(1).lower()
                        declared.add(pkg_name)

    return declared