def partially_unload(self, device_to, memory_to_free=0, force_patch_weights=False):
        with self.use_ejected():
            hooks_unpatched = False
            memory_freed = 0
            patch_counter = 0
            unload_list = self._load_list()
            unload_list.sort()

            offload_buffer = self.model.model_offload_buffer_memory
            if len(unload_list) > 0:
                NS = comfy.model_management.NUM_STREAMS
                offload_weight_factor = [ min(offload_buffer / (NS + 1), unload_list[0][1]) ] * NS

            for unload in unload_list:
                if memory_to_free + offload_buffer - self.model.model_offload_buffer_memory < memory_freed:
                    break
                module_offload_mem, module_mem, n, m, params = unload

                potential_offload = module_offload_mem + sum(offload_weight_factor)

                lowvram_possible = hasattr(m, "comfy_cast_weights")
                if hasattr(m, "comfy_patched_weights") and m.comfy_patched_weights == True:
                    move_weight = True
                    for param in params:
                        key = key_param_name_to_key(n, param)
                        bk = self.backup.get(key, None)
                        if bk is not None:
                            if not lowvram_possible:
                                move_weight = False
                                break

                            if not hooks_unpatched:
                                self.unpatch_hooks()
                                hooks_unpatched = True

                            if bk.inplace_update:
                                comfy.utils.copy_to_param(self.model, key, bk.weight)
                            else:
                                comfy.utils.set_attr_param(self.model, key, bk.weight)
                            self.backup.pop(key)

                    weight_key = "{}.weight".format(n)
                    bias_key = "{}.bias".format(n)
                    if move_weight:
                        cast_weight = self.force_cast_weights
                        m.to(device_to)
                        module_mem += move_weight_functions(m, device_to)
                        if lowvram_possible:
                            if weight_key in self.patches:
                                if force_patch_weights:
                                    self.patch_weight_to_device(weight_key)
                                else:
                                    _, set_func, convert_func = get_key_weight(self.model, weight_key)
                                    m.weight_function.append(LowVramPatch(weight_key, self.patches, convert_func, set_func))
                                    patch_counter += 1
                            if bias_key in self.patches:
                                if force_patch_weights:
                                    self.patch_weight_to_device(bias_key)
                                else:
                                    _, set_func, convert_func = get_key_weight(self.model, bias_key)
                                    m.bias_function.append(LowVramPatch(bias_key, self.patches, convert_func, set_func))
                                    patch_counter += 1
                            cast_weight = True

                        if cast_weight and hasattr(m, "comfy_cast_weights"):
                            m.prev_comfy_cast_weights = m.comfy_cast_weights
                            m.comfy_cast_weights = True
                        m.comfy_patched_weights = False
                        memory_freed += module_mem
                        offload_buffer = max(offload_buffer, potential_offload)
                        offload_weight_factor.append(module_mem)
                        offload_weight_factor.pop(0)
                        logging.debug("freed {}".format(n))

                        for param in params:
                            self.pin_weight_to_device(key_param_name_to_key(n, param))


            self.model.model_lowvram = True
            self.model.lowvram_patch_counter += patch_counter
            self.model.model_loaded_weight_memory -= memory_freed
            self.model.model_offload_buffer_memory = offload_buffer
            logging.info("Unloaded partially: {:.2f} MB freed, {:.2f} MB remains loaded, {:.2f} MB buffer reserved, lowvram patches: {}".format(memory_freed / (1024 * 1024), self.model.model_loaded_weight_memory / (1024 * 1024), offload_buffer / (1024 * 1024), self.model.lowvram_patch_counter))
            return memory_freed