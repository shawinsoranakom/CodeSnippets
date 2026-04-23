def recv_checkpoint(self, src_rank: int) -> object:
        """
        Receive a checkpoint from a source rank.

        The process:
        1. Receives metadata about the checkpoint structure
        2. Receives each tensor, potentially reusing existing tensors for in-place updates
        3. Reconstructs the original state dict structure

        Args:
            src_rank: The source rank to receive the checkpoint from

        Returns:
            The reconstructed state dictionary with model parameters
        """
        state_dict = self._state_dict() if self._state_dict else {}
        state_dict_leaves, _ = tree_flatten_with_path(state_dict)

        dst_tensors: dict[KeyPath, object] = dict(state_dict_leaves)

        len_t = torch.zeros(1, dtype=torch.int64, device=self._device)
        self._pg.recv([len_t], src_rank, tag=1).wait()
        length = cast(int, len_t.item())

        buf = torch.empty(length, dtype=torch.uint8, device=self._device)
        self._pg.recv([buf], src_rank, tag=2).wait()

        meta: _StateDictMeta = pickle.loads(buf.cpu().numpy().tobytes())

        i: int = 0
        works: list[Work] = []

        def recv(path: KeyPath, v: _TensorMeta) -> torch.Tensor:
            nonlocal i

            inplace = dst_tensors.get(path)
            if (
                isinstance(inplace, torch.Tensor)
                and inplace.device.type == self._device.type
            ):
                if isinstance(inplace, DTensor):
                    inplace = inplace._local_tensor
                t = _cast_tensor(inplace, torch.uint8)
                if t.nbytes != v.nbytes:
                    raise AssertionError("inplace tensor storage must be the same size")
            else:
                t = torch.empty(v.nbytes, dtype=torch.uint8, device=self._device)

            work = self._pg.recv([t], src_rank, tag=3 + i)
            i += 1

            if inplace is None:
                # if not inplace we need to copy it to CPU to avoid OOMing
                work.wait()
                t = t.cpu()
            else:
                works.append(work)

            return torch.as_strided(
                t.view(v.dtype),
                size=v.shape,
                stride=v.stride,
                storage_offset=v.storage_offset,
            )

        values: list[object] = []
        for path, v in zip(meta.paths, meta.non_tensor_leaves):
            if isinstance(v, _TensorMeta):
                values.append(recv(path, v))
            elif isinstance(v, _DTensorMeta):
                tensor = recv(path, v.local)
                # pyrefly: ignore [bad-argument-type, bad-argument-count, unexpected-keyword]
                values.append(DTensor(tensor, v.spec, requires_grad=False))
            elif isinstance(v, _ShardedTensorMeta):
                # Receive all local shards that were sent to us
                local_shards = []
                current_rank = self._pg.rank()

                # Receive tensors for each local shard that was sent
                for j, shard_meta in enumerate(v.local_shards_meta):
                    tensor = recv(path, shard_meta)

                    # Use the original shard metadata that was stored during preparation
                    # but update the placement to reflect the current rank/device
                    original_shard_metadata = v.local_shards_shard_metadata[j]
                    updated_shard_metadata = ShardMetadata(
                        shard_offsets=original_shard_metadata.shard_offsets,
                        shard_sizes=original_shard_metadata.shard_sizes,
                        placement=f"rank:{current_rank}/{tensor.device.type}",
                    )

                    local_shard = ShardedTensorShard(
                        tensor=tensor, metadata=updated_shard_metadata
                    )
                    local_shards.append(local_shard)

                # Use complete metadata to reconstruct ShardedTensor
                sharded_tensor = (
                    ShardedTensor._init_from_local_shards_and_global_metadata(
                        local_shards=local_shards,
                        sharded_tensor_metadata=v.sharded_tensor_metadata,
                    )
                )
                values.append(sharded_tensor)
            else:
                values.append(v)

        for work in works:
            work.wait()

        return tree_unflatten(values, meta.treespec)