def cuda(
        self,
        device=None,
        non_blocking=False,
        memory_format=torch.preserve_format,
        process_group=None,
    ) -> ShardedTensor:
        """
        Returns a copy of this object in CUDA memory, if the original ShardedTensor
        is on CPU, we will move the local shard to the current GPU device of each
        process in a SPMD fashion.
        If this ShardedTensor is already on CUDA memory and local shards on each rank are
        already on current device, we still returns a new ShardedTensor object with new
        metadata, but no underlying data movements are performed.
        .. note:: When moving a ShardedTensor from CPU to GPU, the ShardedTensor might
            need to be managed by a different type of ProcessGroup(i.e. ProcessGroupNCCL),
            it is the user's responsibility to explicitly pass in a new process_group that
            is compatible with GPU.
        """
        if (
            memory_format != torch.preserve_format
            and memory_format != torch.contiguous_format
        ):
            raise RuntimeError(
                "Only `torch.contiguous_format` or "
                "`torch.preserve_format` is supported!"
            )

        if device is not None:
            device = torch.device(device) if isinstance(device, str) else device
            if not (
                isinstance(device, torch.device)
                and device.index == torch.cuda.current_device()
            ):
                raise AssertionError(
                    """Only device without device id (e.g. "cpu" or "cuda") is expected for ShardedTensor!"""
                )

        current_device = torch.device(torch.cuda.current_device())
        # returns a copy of ShardedTensor on CUDA current device
        list_shards: list[Shard] = []
        # move all local shards to current device, and change metadata
        # if local shards already on the current device, there's no
        # real data movement, only the metadata are copied.
        for shard in self._local_shards:
            cuda_tensor = shard.tensor.cuda(
                device=current_device,
                non_blocking=non_blocking,
                memory_format=memory_format,
            )  # type: ignore[call-arg]
            metadata = copy.deepcopy(shard.metadata)
            metadata.placement._device = current_device  # type: ignore[union-attr]

            list_shards.append(Shard(cuda_tensor, metadata))

        st_meta = copy.deepcopy(self.metadata())
        for meta in st_meta.shards_metadata:
            if meta.placement.device().type != "cuda":  # type: ignore[union-attr]
                meta.placement._device = current_device  # type: ignore[union-attr]

        pg = self._process_group if process_group is None else process_group
        # we need to use `init_from_local_shards` to communicate between ranks
        # and update the sharding spec/shards metadata.
        st_cuda = ShardedTensor._init_from_local_shards_and_global_metadata(
            list_shards,
            sharded_tensor_metadata=st_meta,
            process_group=pg,
            init_rrefs=self._init_rrefs,
        )
        return st_cuda