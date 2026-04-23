def prepare_hook_patches_current_keyframe(self, t: torch.Tensor, hook_group: comfy.hooks.HookGroup, model_options: dict[str]):
        curr_t = t[0]
        reset_current_hooks = False
        transformer_options = model_options.get("transformer_options", {})
        for hook in hook_group.hooks:
            changed = hook.hook_keyframe.prepare_current_keyframe(curr_t=curr_t, transformer_options=transformer_options)
            # if keyframe changed, remove any cached HookGroups that contain hook with the same hook_ref;
            # this will cause the weights to be recalculated when sampling
            if changed:
                # reset current_hooks if contains hook that changed
                if self.current_hooks is not None:
                    for current_hook in self.current_hooks.hooks:
                        if current_hook == hook:
                            reset_current_hooks = True
                            break
                for cached_group in list(self.cached_hook_patches.keys()):
                    if cached_group.contains(hook):
                        self.cached_hook_patches.pop(cached_group)
        if reset_current_hooks:
            self.patch_hooks(None)