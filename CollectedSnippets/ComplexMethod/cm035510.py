def is_running_in_docker() -> bool:
    """Best-effort detection for Docker containers."""
    docker_env_markers = (
        Path('/.dockerenv'),
        Path('/run/.containerenv'),
    )
    if any(marker.exists() for marker in docker_env_markers):
        return True

    if os.environ.get('DOCKER_CONTAINER') == 'true':
        return True

    try:
        with Path('/proc/self/cgroup').open('r', encoding='utf-8') as cgroup_file:
            for line in cgroup_file:
                if any(token in line for token in ('docker', 'containerd', 'kubepods')):
                    return True
    except FileNotFoundError:
        pass

    return False