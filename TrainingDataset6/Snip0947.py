def run_side_effect(*args, **kwargs):
    container_id = pexpect_docker_run(*args, **kwargs)
    pexpect_docker_stats(container_id)
    return container_id