def _fw_pre_hook(self, mod, input):
        if torch._dynamo.eval_frame._is_in_optimized_module():
            return

        name = self._get_mod_name(mod)
        w_mod = weakref.ref(mod)
        self._get_append_fn(w_mod, name, False)()
        if self._user_pre_fw_hook is not None:
            self._user_pre_fw_hook(mod, input)
        args, _ = tree_flatten(input)
        tensors = [a for a in args if isinstance(a, torch.Tensor) and a.requires_grad]
        if not self.is_bw:
            if tensors:
                register_multi_grad_hook(tensors, self._get_pop_fn(w_mod, name, True))
            else:
                self._post_bw_callbacks_to_enqueue.append(
                    self._get_pop_fn(w_mod, name, True)
                )