def clone(self, disable_dynamic=False, model_override=None):
        class_ = self.__class__
        if self.is_dynamic() and disable_dynamic:
            class_ = ModelPatcher
            if model_override is None:
                if self.cached_patcher_init is None:
                    raise RuntimeError("Cannot create non-dynamic delegate: cached_patcher_init is not initialized.")
                temp_model_patcher = self.cached_patcher_init[0](*self.cached_patcher_init[1], disable_dynamic=True)
                model_override = temp_model_patcher.get_clone_model_override()
        if model_override is None:
            model_override = self.get_clone_model_override()

        n = class_(model_override[0], self.load_device, self.offload_device, self.model_size(), weight_inplace_update=self.weight_inplace_update)
        n.patches = {}
        for k in self.patches:
            n.patches[k] = self.patches[k][:]
        n.patches_uuid = self.patches_uuid

        n.object_patches = self.object_patches.copy()
        n.weight_wrapper_patches = self.weight_wrapper_patches.copy()
        n.model_options = comfy.utils.deepcopy_list_dict(self.model_options)
        n.parent = self

        n.force_cast_weights = self.force_cast_weights

        n.backup, n.backup_buffers, n.object_patches_backup, n.pinned = model_override[1]

        # attachments
        n.attachments = {}
        for k in self.attachments:
            if hasattr(self.attachments[k], "on_model_patcher_clone"):
                n.attachments[k] = self.attachments[k].on_model_patcher_clone()
            else:
                n.attachments[k] = self.attachments[k]
        # additional models
        for k, c in self.additional_models.items():
            n.additional_models[k] = [x.clone() for x in c]
        # callbacks
        for k, c in self.callbacks.items():
            n.callbacks[k] = {}
            for k1, c1 in c.items():
                n.callbacks[k][k1] = c1.copy()
        # sample wrappers
        for k, w in self.wrappers.items():
            n.wrappers[k] = {}
            for k1, w1 in w.items():
                n.wrappers[k][k1] = w1.copy()
        # injection
        n.is_injected = self.is_injected
        n.skip_injection = self.skip_injection
        for k, i in self.injections.items():
            n.injections[k] = i.copy()
        # hooks
        n.hook_patches = create_hook_patches_clone(self.hook_patches)
        n.hook_patches_backup = create_hook_patches_clone(self.hook_patches_backup) if self.hook_patches_backup else self.hook_patches_backup
        for group in self.cached_hook_patches:
            n.cached_hook_patches[group] = {}
            for k in self.cached_hook_patches[group]:
                n.cached_hook_patches[group][k] = self.cached_hook_patches[group][k]
        n.hook_backup = self.hook_backup
        n.current_hooks = self.current_hooks.clone() if self.current_hooks else self.current_hooks
        n.forced_hooks = self.forced_hooks.clone() if self.forced_hooks else self.forced_hooks
        n.is_clip = self.is_clip
        n.hook_mode = self.hook_mode

        n.cached_patcher_init = self.cached_patcher_init

        for callback in self.get_all_callbacks(CallbacksMP.ON_CLONE):
            callback(self, n)
        return n