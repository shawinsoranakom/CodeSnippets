def add_dp_placement_groups(
        old_vllm_config: VllmConfig, new_data_parallel_size: int
    ) -> tuple[list["PlacementGroup"], list[int]]:
        """
        Add placement groups for new data parallel size.
        """
        import ray
        from ray._private.state import (
            available_resources_per_node,
            total_resources_per_node,
        )
        from ray.util.state import list_nodes

        old_dp_size = old_vllm_config.parallel_config.data_parallel_size
        num_pg_to_create = new_data_parallel_size - old_dp_size

        if num_pg_to_create <= 0:
            return [], []

        dp_master_ip = old_vllm_config.parallel_config.data_parallel_master_ip
        world_size = old_vllm_config.parallel_config.world_size

        nodes = list_nodes()
        nodes = sorted(nodes, key=lambda node: node.node_ip != dp_master_ip)
        assert nodes[0].node_ip == dp_master_ip, "The first node must be the head node"
        assert len(nodes) == 1 or nodes[1].node_ip != dp_master_ip, (
            "There can only be one head node"
        )

        available_resources = available_resources_per_node()
        total_resources = total_resources_per_node()

        placement_groups = []
        local_dp_ranks = []
        num_pg_created = 0

        device_str = current_platform.ray_device_key
        for node in nodes:
            if num_pg_created >= num_pg_to_create:
                break

            node_ip = node.node_ip
            node_id = node.node_id
            if device_str not in available_resources[node_id]:
                continue
            available_gpus = int(available_resources[node_id][device_str])

            # Get total GPUs on this node from the node's resources
            # Ray stores node resources with node ID as key
            total_gpus = int(total_resources[node_id][device_str])

            # Calculate used GPUs and used engines on this node
            used_gpus = max(0, total_gpus - available_gpus)
            used_engines_on_node = used_gpus // world_size

            # Calculate how many new engines this node can accommodate
            available_engine_count = available_gpus // world_size

            # Create placement groups for new engines on this node
            for i in range(available_engine_count):
                if num_pg_created >= num_pg_to_create:
                    break

                rank = old_dp_size + num_pg_created

                # Create bundles with node constraint for master node
                if node_ip == dp_master_ip:
                    bundles = [
                        {device_str: 1.0, "node:" + dp_master_ip: 0.001}
                    ] * world_size + [{"CPU": 1.0}]
                else:
                    bundles = [{device_str: 1.0}] * world_size + [{"CPU": 1.0}]

                pg = ray.util.placement_group(
                    name=f"dp_rank_{rank}",
                    strategy="STRICT_PACK",
                    bundles=bundles,
                )
                placement_groups.append(pg)

                # Local rank starts from the number of engines already used
                # on this node
                local_rank = used_engines_on_node + i
                local_dp_ranks.append(local_rank)
                num_pg_created += 1

        return placement_groups, local_dp_ranks