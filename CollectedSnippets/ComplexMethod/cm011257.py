def to(self, *args, **kwargs) -> ShardedTensor:
        current_device: torch.device
        if self._local_shards:
            current_device = self._local_shards[0].tensor.device
        elif self._process_group._get_backend_name() == "gloo":
            current_device = torch.device("cpu")
        else:
            current_device = torch.device(torch.cuda.current_device())
        current_dtype = self.dtype
        device_to = current_device
        dtype_to = current_dtype
        if len(args) == 1:
            if isinstance(args[0], torch.dtype):
                dtype_to = args[0]
            elif isinstance(args[0], torch.device):
                device_to = args[0]
            elif isinstance(args[0], (str, int)):
                device_to = torch.device(args[0])
            elif isinstance(args[0], torch.Tensor):
                dtype_to = args[0].dtype
                device_to = args[0].device
            else:
                raise RuntimeError(f"ShardedTensor.to() have wrong arguments: {args}")
        elif len(args) == 2:
            device_to, dtype_to = args
        else:
            dtype_to = kwargs.get("dtype", current_dtype)
            device_to = kwargs.get("device", current_device)

        device_to = (
            torch.device(device_to) if isinstance(device_to, (str, int)) else device_to
        )

        if device_to.type == "cuda":
            # if device_to set to cuda, set to current device even
            # if user specify the device index.
            current_idx = torch.cuda.current_device()
            if device_to.index != current_idx:
                warnings.warn(
                    "ShardedTensor.to only move tensor to its current device"
                    "If you want to put to different device, use `reshard` instead.",
                    stacklevel=2,
                )
            device_to = torch.device(current_idx)

        copy_tensor = kwargs.get("copy", False)
        non_blocking = kwargs.get("non_blocking", False)
        memory_format = kwargs.get("memory_format", torch.preserve_format)
        process_group = kwargs.get("process_group")

        if (
            not copy_tensor
            and dtype_to == current_dtype
            and device_to == current_device
        ):
            # already have correct dtype and device, return itself
            return self

        # returns a copy of ShardedTensor on CUDA current device
        list_shards: list[Shard] = []

        for shard in self._local_shards:
            new_tensor = shard.tensor.to(  # type: ignore[call-overload]
                device=device_to,
                dtype=dtype_to,
                non_blocking=non_blocking,
                copy=copy_tensor,
                memory_format=memory_format,
            )
            metadata = copy.deepcopy(shard.metadata)
            if metadata.placement is not None:
                metadata.placement._device = device_to
            list_shards.append(Shard(new_tensor, metadata))

        # update metadata
        st_meta = copy.deepcopy(self.metadata())
        st_meta.tensor_properties.dtype = dtype_to
        for meta in st_meta.shards_metadata:
            meta.placement._device = device_to  # type: ignore[union-attr]

        pg = self._process_group if process_group is None else process_group
        # we need to use `init_from_local_shards` to communicate between ranks
        # and update the sharding spec/shards metadata.
        st_to = ShardedTensor._init_from_local_shards_and_global_metadata(
            list_shards,
            sharded_tensor_metadata=st_meta,
            process_group=pg,
            init_rrefs=self._init_rrefs,
        )
        return st_to