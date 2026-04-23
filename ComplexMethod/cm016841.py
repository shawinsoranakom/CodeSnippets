def apply_cache_diff(self, x: torch.Tensor, uuids: list[UUID], is_audio: bool = False):
        if self.first_cond_uuid in uuids and not is_audio:
            self.total_steps_skipped += 1
        cache_diffs = self.uuid_cache_diffs_audio if is_audio else self.uuid_cache_diffs
        batch_offset = x.shape[0] // len(uuids)
        for i, uuid in enumerate(uuids):
            # slice out only what is relevant to this cond
            batch_slice = [slice(i*batch_offset,(i+1)*batch_offset)]
            # if cached dims don't match x dims, cut off excess and hope for the best (cosmos world2video)
            if x.shape[1:] != cache_diffs[uuid].shape[1:]:
                if not self.allow_mismatch:
                    raise ValueError(f"Cached dims {self.uuid_cache_diffs[uuid].shape} don't match x dims {x.shape} - this is no good")
                slicing = []
                skip_this_dim = True
                for dim_u, dim_x in zip(cache_diffs[uuid].shape, x.shape):
                    if skip_this_dim:
                        skip_this_dim = False
                        continue
                    if dim_u != dim_x:
                        if self.cut_from_start:
                            slicing.append(slice(dim_x-dim_u, None))
                        else:
                            slicing.append(slice(None, dim_u))
                    else:
                        slicing.append(slice(None))
                batch_slice = batch_slice + slicing
            x[tuple(batch_slice)] += cache_diffs[uuid].to(x.device)
        return x