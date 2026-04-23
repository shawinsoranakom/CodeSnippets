def read_data(self, plan: LoadPlan, planner: LoadPlanner) -> Future[None]:
        """
        Reads torch save data on the coordinator rank, and broadcast afterwards
        this incurrs a communication cost, but avoids having to load
        the entire checkpoint on each rank, hopefully preventing OOM issues
        """
        planner = cast(DefaultLoadPlanner, planner)

        # data is read in on the coordinator rank, and broadcast afterwards
        # this incurs a communication cost, but it avoids having to load
        # the entire checkpoint on each rank, hopefully preventing OOM issues
        # TODO: read on each host, instead of only the coordinator
        if self.is_coordinator:
            if self.checkpoint_id is None:
                raise AssertionError("checkpoint_id must be set before reading data")
            torch_state_dict = torch.load(
                self.checkpoint_id, map_location="cpu", weights_only=False
            )
            if planner.flatten_state_dict:
                torch_state_dict, _ = flatten_state_dict(torch_state_dict)
        else:
            torch_state_dict = None

        for req in plan.items:
            if req.type == LoadItemType.BYTE_IO:
                raise RuntimeError(
                    f"Non-tensor value identified at {req.storage_index.fqn}. "
                    f"At this time {type(self).__name__} only supports loading Tensors."
                )

            #  Broadcast the tensor from the coordinator rank
            if self.is_coordinator:
                pg_device = dist.distributed_c10d._get_pg_default_device()
                # pyrefly: ignore [unsupported-operation]
                tensor = torch_state_dict[req.storage_index.fqn].to(pg_device)
            else:
                tensor = torch.empty_like(planner.state_dict[req.storage_index.fqn])

            dist.broadcast(tensor, src=self.coordinator_rank, async_op=False)

            tensor = narrow_tensor_by_index(tensor, req.storage_offsets, req.lengths)
            target_tensor = planner.resolve_tensor(req).detach()
            if not target_tensor.size() == tensor.size():
                raise AssertionError(
                    f"req {req.storage_index} mismatch sizes, "
                    f"{target_tensor.size()} vs {tensor.size()}"
                )
            target_tensor.copy_(tensor)
            planner.commit_tensor(req, target_tensor)

        fut: Future = Future()
        fut.set_result(None)
        return fut