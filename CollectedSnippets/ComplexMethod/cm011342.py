def read_data(self, plan: LoadPlan, planner: LoadPlanner) -> Future[None]:
        # group requests by file
        per_file: dict[str, list[ReadItem]] = {}
        for read_item in plan.items:
            item_md: _StorageInfo = self.storage_data[read_item.storage_index]
            path = item_md.relative_path
            per_file.setdefault(path, []).append(read_item)

        for relative_path, reqs in per_file.items():
            new_path = self.fs.concat_path(self.path, relative_path)
            with self.fs.create_stream(new_path, "rb") as stream:
                # TODO sort by offset and cache the reading
                for req in reqs:
                    item_md = self.storage_data[req.storage_index]
                    file_slice = self._slice_file(stream, item_md)
                    transform_from = self.transforms.transform_load_stream(
                        req,
                        # This field wasn't present in older
                        # implementations so provide a fallback.
                        item_md.transform_descriptors or (),
                        file_slice,
                    )

                    if req.type == LoadItemType.BYTE_IO:
                        read_bytes = io.BytesIO(transform_from.read(-1))
                        read_bytes.seek(0)
                        planner.load_bytes(req, read_bytes)
                    else:
                        if transform_from.seekable():
                            seekable = transform_from
                        else:
                            # torch.load requires a seekable input, so read the transform
                            # stream now and store the output if needed
                            seekable = io.BytesIO(transform_from.read(-1))
                            seekable.seek(0)

                        tensor = cast(
                            Tensor,
                            torch.load(
                                seekable,
                                map_location="cpu",
                                weights_only=True,
                            ),
                        )
                        tensor = narrow_tensor_by_index(
                            tensor, req.storage_offsets, req.lengths
                        )
                        target_tensor = planner.resolve_tensor(req).detach()

                        if target_tensor.size() != tensor.size():
                            raise AssertionError(
                                f"req {req.storage_index} mismatch sizes {target_tensor.size()} vs {tensor.size()}"
                            )
                        target_tensor.copy_(tensor)
                        planner.commit_tensor(req, target_tensor)

        fut: Future = Future()
        fut.set_result(None)
        return fut