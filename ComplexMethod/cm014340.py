def hook(_, grad_output):
                self.grad_outputs = self._pack_with_none(self.output_tensors_index,
                                                         grad_output,
                                                         self.n_outputs)

                if self.user_pre_hooks:
                    expected_len = len(self.grad_outputs)
                    for user_pre_hook in self.user_pre_hooks:
                        hook_grad_outputs = user_pre_hook(self.module, self.grad_outputs)
                        if hook_grad_outputs is None:
                            continue

                        actual_len = len(hook_grad_outputs)
                        if actual_len != expected_len:
                            raise RuntimeError("Backward pre hook returned an invalid number of grad_output, "
                                               f"got {actual_len}, but expected {expected_len}")
                        self.grad_outputs = hook_grad_outputs

                # We need to be able to clear self.grad_outputs but also return it
                local_grad_outputs = self.grad_outputs

                # Special case if no input required gradients, this hook should call the user
                # hook directly
                if self.input_tensors_index is None:
                    warnings.warn("Full backward hook is firing when gradients are computed "
                                  "with respect to module outputs since no inputs require gradients. See "
                                  "https://docs.pytorch.org/docs/main/generated/torch.nn.Module.html#torch.nn.Module.register_full_backward_hook "
                                  "for more details.",
                                  stacklevel=5)
                    grad_inputs = self._pack_with_none([], [], self.n_inputs)
                    for user_hook in self.user_hooks:
                        res = user_hook(self.module, grad_inputs, self.grad_outputs)
                        if res is not None and not (isinstance(res, tuple) and all(el is None for el in res)):
                            raise RuntimeError("Backward hook for Modules where no input requires "
                                               "gradient should always return None or None for all gradients.")
                    self.grad_outputs = None

                if local_grad_outputs is not None:
                    if self.output_tensors_index is None:
                        raise AssertionError("output_tensors_index should not be None when grad_outputs is not None")
                    return tuple(local_grad_outputs[i] for i in self.output_tensors_index)