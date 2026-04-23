def partially_load(self, device_to, extra_memory=0, force_patch_weights=False):
        with self.use_ejected(skip_and_inject_on_exit_only=True):
            unpatch_weights = self.model.current_weight_patches_uuid is not None and (self.model.current_weight_patches_uuid != self.patches_uuid or force_patch_weights)
            # TODO: force_patch_weights should not unload + reload full model
            used = self.model.model_loaded_weight_memory
            self.unpatch_model(self.offload_device, unpatch_weights=unpatch_weights)
            if unpatch_weights:
                extra_memory += (used - self.model.model_loaded_weight_memory)

            self.patch_model(load_weights=False)
            if extra_memory < 0 and not unpatch_weights:
                self.partially_unload(self.offload_device, -extra_memory, force_patch_weights=force_patch_weights)
                return 0
            full_load = False
            if self.model.model_lowvram == False and self.model.model_loaded_weight_memory > 0:
                self.apply_hooks(self.forced_hooks, force_apply=True)
                return 0
            if self.model.model_loaded_weight_memory + extra_memory > self.model_size():
                full_load = True
            current_used = self.model.model_loaded_weight_memory
            try:
                self.load(device_to, lowvram_model_memory=current_used + extra_memory, force_patch_weights=force_patch_weights, full_load=full_load)
            except Exception as e:
                self.detach()
                raise e

            return self.model.model_loaded_weight_memory - current_used