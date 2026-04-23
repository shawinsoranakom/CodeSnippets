def pack_hook(x):
            x = x.detach() if x.requires_grad else x
            target_frame = target_frame_ref()
            if target_frame is None:
                raise AssertionError("Internal error: target_frame reference is None")
            recomp_idx = target_frame.recomp_counter[gid]
            target_frame.recomp_counter[gid] += 1

            if recomp_idx >= len(target_frame.weak_holders):
                if target_frame.early_stop:
                    raise AssertionError("Unexpected state: target_frame.early_stop is set")
                if not target_frame.forward_completed:
                    # We run into this case when early stop is not enabled and do
                    # grad within checkpoint.
                    # We need to set this flag, so we don't error out later when
                    # we check if the number of tensors saved during forward and
                    # recomputation match.
                    target_frame.ignore_saved_mismatch = True
                    return x
                raise CheckpointError(
                    "torch.utils.checkpoint: trying to save more tensors during "
                    "recomputation than during the original forward pass.\n"
                    f"{_debug_tip_msg}"
                )

            holder = target_frame.weak_holders[recomp_idx]()

            # This holder may have been cleared because someone may have called
            # backward within forward. If so, we don't need to save.
            if holder is not None:
                _internal_assert(holder.handles.get(gid, None) is None)
                holder.handles[gid] = _Handle()
                target_frame.recomputed[gid][holder.handles[gid]] = x

            if target_frame.early_stop and target_frame.recomp_counter[gid] == len(
                target_frame.weak_holders
            ):
                raise _StopRecomputationError
            # See Rule 6: [ retain_graph is True ] above
            return x