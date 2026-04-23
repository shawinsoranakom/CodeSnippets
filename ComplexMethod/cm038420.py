def irecv_tensor_dict(
        self,
        src: int | None = None,
        all_gather_group: "GroupCoordinator | None" = None,
        all_gather_tensors: dict[str, bool] | None = None,
    ) -> tuple[
        dict[str, torch.Tensor | Any] | None,
        list[Handle],
        list[Callable[[], None]],
    ]:
        if not torch.distributed.is_initialized() or self.world_size == 1:
            return None, [], []

        if src is None:
            src = (self.rank_in_group - 1) % self.world_size
        assert src < self.world_size, f"Invalid src rank ({src})"

        if self.use_cpu_custom_send_recv:
            if self.device_communicator is None:
                raise ValueError("No device communicator found")
            # custom device communicator path is synchronous
            sync_tensor_dict = self.device_communicator.recv_tensor_dict(  # type: ignore
                src
            )
            return sync_tensor_dict, [], []

        all_gather_size = 1 if all_gather_group is None else all_gather_group.world_size
        all_gather_rank = (
            0 if all_gather_group is None else all_gather_group.rank_in_group
        )

        group = self.device_group
        metadata_group = self.cpu_group

        recv_metadata_list = self.recv_object(src=src)
        tensor_dict: dict[str, Any] = {}
        handles: list[Handle] = []
        postprocess: list[Callable[[], None]] = []

        for key, value in recv_metadata_list:
            if isinstance(value, TensorMetadata):
                full_tensor = torch.empty(
                    value.size, dtype=value.dtype, device=value.device
                )
                if full_tensor.numel() == 0:
                    tensor_dict[key] = full_tensor
                    continue

                if self._should_use_all_gather(
                    key, full_tensor.numel(), all_gather_group, all_gather_tensors
                ):
                    orig_shape = full_tensor.shape
                    slice_tensor = full_tensor.reshape(all_gather_size, -1)[
                        all_gather_rank
                    ]
                    comm_group = metadata_group if slice_tensor.is_cpu else group
                    handle = torch.distributed.irecv(
                        slice_tensor, src=self.ranks[src], group=comm_group
                    )
                    handles.append(handle)

                    def _postprocess(
                        key: str = key,
                        slice_tensor: torch.Tensor = slice_tensor,
                        orig_shape: tuple[int, ...] = tuple(orig_shape),
                        all_gather_group=all_gather_group,
                    ) -> None:
                        assert all_gather_group is not None
                        tensor_dict[key] = all_gather_group.all_gather(
                            slice_tensor, dim=0
                        ).reshape(orig_shape)

                    postprocess.append(_postprocess)
                    tensor_dict[key] = slice_tensor
                else:
                    comm_group = metadata_group if full_tensor.is_cpu else group
                    handle = torch.distributed.irecv(
                        full_tensor, src=self.ranks[src], group=comm_group
                    )
                    handles.append(handle)
                    tensor_dict[key] = full_tensor
            else:
                tensor_dict[key] = value

        return tensor_dict, handles, postprocess