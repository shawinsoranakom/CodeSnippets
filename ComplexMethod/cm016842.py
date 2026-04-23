def update_cache_diff(self, output: torch.Tensor, x: torch.Tensor, uuids: list[UUID], is_audio: bool = False):
        cache_diffs = self.uuid_cache_diffs_audio if is_audio else self.uuid_cache_diffs
        # if output dims don't match x dims, cut off excess and hope for the best (cosmos world2video)
        if output.shape[1:] != x.shape[1:]:
            if not self.allow_mismatch:
                raise ValueError(f"Output dims {output.shape} don't match x dims {x.shape} - this is no good")
            slicing = []
            skip_dim = True
            for dim_o, dim_x in zip(output.shape, x.shape):
                if not skip_dim and dim_o != dim_x:
                    if self.cut_from_start:
                        slicing.append(slice(dim_x-dim_o, None))
                    else:
                        slicing.append(slice(None, dim_o))
                else:
                    slicing.append(slice(None))
                skip_dim = False
            x = x[tuple(slicing)]
        diff = output - x
        batch_offset = diff.shape[0] // len(uuids)
        for i, uuid in enumerate(uuids):
            cache_diffs[uuid] = diff[i*batch_offset:(i+1)*batch_offset, ...]