def set_backward_flags(_model: nn.Module, is_last_microbatch: bool):
            if mode == "all":
                set_grad_sync_flag(_model, is_last_microbatch)
                if not reshard_after_backward:
                    _model.set_reshard_after_backward(is_last_microbatch)
            elif mode == "some_mlps":
                for mlp in model[1 : 1 + num_mlps_to_disable_reduce_scatter]:
                    set_grad_sync_flag(mlp, is_last_microbatch)
                    if not reshard_after_backward:
                        mlp.set_reshard_after_backward(is_last_microbatch)
            elif mode == "root_only":
                set_grad_sync_flag(model, is_last_microbatch, recurse=False)
                if not reshard_after_backward:
                    model.set_reshard_after_backward(is_last_microbatch, recurse=False)