def load(self, device_to=None, lowvram_model_memory=0, force_patch_weights=False, full_load=False):
        with self.use_ejected():
            self.unpatch_hooks()
            mem_counter = 0
            patch_counter = 0
            lowvram_counter = 0
            lowvram_mem_counter = 0
            loading = self._load_list()

            load_completely = []
            offloaded = []
            offload_buffer = 0
            loading.sort(reverse=True)
            for i, x in enumerate(loading):
                module_offload_mem, module_mem, n, m, params = x

                lowvram_weight = False

                potential_offload = max(offload_buffer, module_offload_mem + sum([ x1[1] for x1 in loading[i+1:i+1+comfy.model_management.NUM_STREAMS]]))
                lowvram_fits = mem_counter + module_mem + potential_offload < lowvram_model_memory

                weight_key = "{}.weight".format(n)
                bias_key = "{}.bias".format(n)

                if not full_load and hasattr(m, "comfy_cast_weights"):
                    if not lowvram_fits:
                        offload_buffer = potential_offload
                        lowvram_weight = True
                        lowvram_counter += 1
                        lowvram_mem_counter += module_mem
                        if hasattr(m, "prev_comfy_cast_weights"): #Already lowvramed
                            continue

                cast_weight = self.force_cast_weights
                m.comfy_force_cast_weights = self.force_cast_weights
                if lowvram_weight:
                    if hasattr(m, "comfy_cast_weights"):
                        m.weight_function = []
                        m.bias_function = []

                    if weight_key in self.patches:
                        if force_patch_weights:
                            self.patch_weight_to_device(weight_key)
                        else:
                            _, set_func, convert_func = get_key_weight(self.model, weight_key)
                            m.weight_function = [LowVramPatch(weight_key, self.patches, convert_func, set_func)]
                            patch_counter += 1
                    if bias_key in self.patches:
                        if force_patch_weights:
                            self.patch_weight_to_device(bias_key)
                        else:
                            _, set_func, convert_func = get_key_weight(self.model, bias_key)
                            m.bias_function = [LowVramPatch(bias_key, self.patches, convert_func, set_func)]
                            patch_counter += 1

                    cast_weight = True
                    offloaded.append((module_mem, n, m, params))
                else:
                    if hasattr(m, "comfy_cast_weights"):
                        wipe_lowvram_weight(m)

                    if full_load or lowvram_fits:
                        mem_counter += module_mem
                        load_completely.append((module_mem, n, m, params))
                    else:
                        offload_buffer = potential_offload

                if cast_weight and hasattr(m, "comfy_cast_weights"):
                    m.prev_comfy_cast_weights = m.comfy_cast_weights
                    m.comfy_cast_weights = True

                if weight_key in self.weight_wrapper_patches:
                    m.weight_function.extend(self.weight_wrapper_patches[weight_key])

                if bias_key in self.weight_wrapper_patches:
                    m.bias_function.extend(self.weight_wrapper_patches[bias_key])

                mem_counter += move_weight_functions(m, device_to)

            load_completely.sort(reverse=True)
            for x in load_completely:
                n = x[1]
                m = x[2]
                params = x[3]
                if hasattr(m, "comfy_patched_weights"):
                    if m.comfy_patched_weights == True:
                        continue

                for param in params:
                    key = key_param_name_to_key(n, param)
                    self.unpin_weight(key)
                    self.patch_weight_to_device(key, device_to=device_to)
                if comfy.model_management.is_device_cuda(device_to):
                    torch.cuda.synchronize()

                logging.debug("lowvram: loaded module regularly {} {}".format(n, m))
                m.comfy_patched_weights = True

            for x in load_completely:
                x[2].to(device_to)

            for x in offloaded:
                n = x[1]
                params = x[3]
                for param in params:
                    self.pin_weight_to_device(key_param_name_to_key(n, param))

            usable_stat = "{:.2f} MB usable,".format(lowvram_model_memory / (1024 * 1024)) if lowvram_model_memory < 1e32 else ""
            if lowvram_counter > 0:
                logging.info("loaded partially; {} {:.2f} MB loaded, {:.2f} MB offloaded, {:.2f} MB buffer reserved, lowvram patches: {}".format(usable_stat, mem_counter / (1024 * 1024), lowvram_mem_counter / (1024 * 1024), offload_buffer / (1024 * 1024), patch_counter))
                self.model.model_lowvram = True
            else:
                logging.info("loaded completely; {} {:.2f} MB loaded, full load: {}".format(usable_stat, mem_counter / (1024 * 1024), full_load))
                self.model.model_lowvram = False
                if full_load:
                    self.model.to(device_to)
                    mem_counter = self.model_size()

            self.model.lowvram_patch_counter += patch_counter
            self.model.device = device_to
            self.model.model_loaded_weight_memory = mem_counter
            self.model.model_offload_buffer_memory = offload_buffer
            self.model.current_weight_patches_uuid = self.patches_uuid

            for callback in self.get_all_callbacks(CallbacksMP.ON_LOAD):
                callback(self, device_to, lowvram_model_memory, force_patch_weights, full_load)

            self.apply_hooks(self.forced_hooks, force_apply=True)