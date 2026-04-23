def _fw_post_hook(self, mod, input, output):
        if torch._dynamo.eval_frame._is_in_optimized_module():
            return

        name = self._get_mod_name(mod)
        w_mod = weakref.ref(mod)
        if self._user_post_fw_hook is not None:
            self._user_post_fw_hook(mod, input, output)
        self._get_pop_fn(w_mod, name, False)()
        args, _ = tree_flatten(output)
        tensors = [a for a in args if isinstance(a, torch.Tensor) and a.requires_grad]
        if not self.is_bw and tensors:
            register_multi_grad_hook(
                tensors, self._get_append_fn(w_mod, name, True), mode="any"
            )