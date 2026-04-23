def cpu(
        self, memory_format=torch.preserve_format, process_group=None
    ) -> ShardedTensor:
        """
        Returns a copy of this object in CPU memory.

        If this ShardedTensor is already on CPU memory, then no copy is
        performed and original object is returned.

        .. note:: When moving a ShardedTensor from GPU to CPU, the ShardedTensor might
            need to be managed by a different type of ProcessGroup(i.e. ProcessGroupGloo),
            it is the user's responsibility to explicitly pass in a new process_group that
            is compatible with CPU.
        """
        # TODO: make this a __torch_function__ op once ShardedTensor becomes a
        # torch.Tensor subclass, see https://github.com/pytorch/pytorch/issues/75402
        if (
            memory_format != torch.preserve_format
            and memory_format != torch.contiguous_format
        ):
            raise RuntimeError(
                "Only `torch.contiguous_format` or "
                "`torch.preserve_format` is supported!"
            )
        all_on_cpu = True
        for meta in self.metadata().shards_metadata:
            all_on_cpu &= meta.placement.device().type == "cpu"  # type: ignore[union-attr]

        # if every shard is already on CPU, return the original object
        if all_on_cpu:
            return self

        # if not, returns a copy of this object on CPU
        list_shards: list[Shard] = []
        # move all local shards to cpu, and change metadata
        for shard in self._local_shards:
            cpu_tensor = shard.tensor.cpu(memory_format=memory_format)  # type: ignore[call-arg]
            metadata = copy.deepcopy(shard.metadata)
            metadata.placement._device = torch.device("cpu")  # type: ignore[union-attr]
            list_shards.append(Shard(cpu_tensor, metadata))

        st_meta = copy.deepcopy(self.metadata())
        for meta in st_meta.shards_metadata:
            if meta.placement.device().type != "cpu":  # type: ignore[union-attr]
                meta.placement._device = torch.device("cpu")  # type: ignore[union-attr]

        pg = self._process_group if process_group is None else process_group
        st_cpu = ShardedTensor._init_from_local_shards_and_global_metadata(
            list_shards,
            sharded_tensor_metadata=st_meta,
            process_group=pg,
            init_rrefs=self._init_rrefs,
        )
        return st_cpu