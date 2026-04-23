def patch_hooks(self, hooks: comfy.hooks.HookGroup):
        with self.use_ejected():
            if hooks is not None:
                model_sd_keys = list(self.model_state_dict().keys())
                memory_counter = None
                if self.hook_mode == comfy.hooks.EnumHookMode.MaxSpeed:
                    # TODO: minimum_counter should have a minimum that conforms to loaded model requirements
                    memory_counter = MemoryCounter(initial=comfy.model_management.get_free_memory(self.load_device),
                                                minimum=comfy.model_management.minimum_inference_memory()*2)
                # if have cached weights for hooks, use it
                cached_weights = self.cached_hook_patches.get(hooks, None)
                if cached_weights is not None:
                    model_sd_keys_set = set(model_sd_keys)
                    for key in cached_weights:
                        if key not in model_sd_keys:
                            logging.warning(f"Cached hook could not patch. Key does not exist in model: {key}")
                            continue
                        self.patch_cached_hook_weights(cached_weights=cached_weights, key=key, memory_counter=memory_counter)
                        model_sd_keys_set.remove(key)
                    self.unpatch_hooks(model_sd_keys_set)
                else:
                    self.unpatch_hooks()
                    relevant_patches = self.get_combined_hook_patches(hooks=hooks)
                    original_weights = None
                    if len(relevant_patches) > 0:
                        original_weights = self.get_key_patches()
                    for key in relevant_patches:
                        if key not in model_sd_keys:
                            logging.warning(f"Cached hook would not patch. Key does not exist in model: {key}")
                            continue
                        self.patch_hook_weight_to_device(hooks=hooks, combined_patches=relevant_patches, key=key, original_weights=original_weights,
                                                            memory_counter=memory_counter)
            else:
                self.unpatch_hooks()
            self.current_hooks = hooks