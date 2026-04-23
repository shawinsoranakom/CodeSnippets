def get_visible_memory_node() -> list[int]:
    if platform.system() == "Darwin":
        return [0]

    allowed_memory_node_list = get_memory_affinity()

    env_key = DEVICE_CONTROL_ENV_VAR
    if (
        ("VLLM_CPU_SIM_MULTI_NUMA" not in os.environ)
        and env_key in os.environ
        and os.environ[env_key] != ""
    ):
        visible_nodes = [int(s) for s in os.environ[env_key].split(",")]
        visible_nodes = [
            node for node in visible_nodes if node in allowed_memory_node_list
        ]
        return visible_nodes

    return allowed_memory_node_list