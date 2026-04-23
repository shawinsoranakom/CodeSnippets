def load(self, device_to=None, lowvram_model_memory=0, force_patch_weights=False, full_load=False, dirty=False):

        #Force patching doesn't make sense in Dynamic loading, as you dont know what does and
        #doesn't need to be forced at this stage. The only thing you could do would be patch
        #it all on CPU which consumes huge RAM.
        assert not force_patch_weights

        #Full load doesn't make sense as we dont actually have any loader capability here and
        #now.
        assert not full_load

        assert device_to == self.load_device

        num_patches = 0
        allocated_size = 0
        self.model.model_loaded_weight_memory = 0

        with self.use_ejected():
            self.unpatch_hooks()

            vbar = self._vbar_get(create=True)
            if vbar is not None:
                vbar.prioritize()

            loading = self._load_list(for_dynamic=True, default_device=device_to)
            loading.sort()

            for x in loading:
                *_, module_mem, n, m, params = x

                def set_dirty(item, dirty):
                    if dirty or not hasattr(item, "_v_signature"):
                        item._v_signature = None

                def setup_param(self, m, n, param_key):
                    nonlocal num_patches
                    key = key_param_name_to_key(n, param_key)

                    weight_function = []

                    weight, _, _ = get_key_weight(self.model, key)
                    if weight is None:
                        return (False, 0)
                    if key in self.patches:
                        if comfy.lora.calculate_shape(self.patches[key], weight, key) != weight.shape:
                            return (True, 0)
                        setattr(m, param_key + "_lowvram_function", LowVramPatch(key, self.patches))
                        num_patches += 1
                    else:
                        setattr(m, param_key + "_lowvram_function", None)

                    if key in self.weight_wrapper_patches:
                        weight_function.extend(self.weight_wrapper_patches[key])
                    setattr(m, param_key + "_function", weight_function)
                    geometry = weight
                    if not isinstance(weight, QuantizedTensor):
                        model_dtype = getattr(m, param_key + "_comfy_model_dtype", None) or weight.dtype
                        weight._model_dtype = model_dtype
                        geometry = comfy.memory_management.TensorGeometry(shape=weight.shape, dtype=model_dtype)
                    return (False, comfy.memory_management.vram_aligned_size(geometry))

                def force_load_param(self, param_key, device_to):
                    key = key_param_name_to_key(n, param_key)
                    if key in self.backup:
                        comfy.utils.set_attr_param(self.model, key, self.backup[key].weight)
                    self.patch_weight_to_device(key, device_to=device_to, force_cast=True)
                    weight, _, _ = get_key_weight(self.model, key)
                    if weight is not None:
                        self.model.model_loaded_weight_memory += weight.numel() * weight.element_size()

                if hasattr(m, "comfy_cast_weights"):
                    m.comfy_cast_weights = True
                    m.pin_failed = False
                    m.seed_key = n
                    set_dirty(m, dirty)

                    force_load, v_weight_size = setup_param(self, m, n, "weight")
                    force_load_bias, v_weight_bias = setup_param(self, m, n, "bias")
                    force_load = force_load or force_load_bias
                    v_weight_size += v_weight_bias

                    if force_load:
                        logging.info(f"Module {n} has resizing Lora - force loading")
                        force_load_param(self, "weight", device_to)
                        force_load_param(self, "bias", device_to)
                    else:
                        if vbar is not None and not hasattr(m, "_v"):
                            m._v = vbar.alloc(v_weight_size)
                        allocated_size += v_weight_size

                    for param in params:
                        if param not in ("weight", "bias"):
                            force_load_param(self, param, device_to)

                else:
                    for param in params:
                        key = key_param_name_to_key(n, param)
                        weight, _, _ = get_key_weight(self.model, key)
                        if key not in self.backup:
                            self.backup[key] = collections.namedtuple('Dimension', ['weight', 'inplace_update'])(weight, False)
                        model_dtype = getattr(m, param + "_comfy_model_dtype", None)
                        casted_weight = weight.to(dtype=model_dtype, device=device_to)
                        comfy.utils.set_attr_param(self.model, key, casted_weight)
                        self.model.model_loaded_weight_memory += casted_weight.numel() * casted_weight.element_size()

                move_weight_functions(m, device_to)

            for key, buf in self.model.named_buffers(recurse=True):
                if key not in self.backup_buffers:
                    self.backup_buffers[key] = buf
                module, buf_name = comfy.utils.resolve_attr(self.model, key)
                model_dtype = getattr(module, buf_name + "_comfy_model_dtype", None)
                casted_buf = buf.to(dtype=model_dtype, device=device_to)
                comfy.utils.set_attr_buffer(self.model, key, casted_buf)
                self.model.model_loaded_weight_memory += casted_buf.numel() * casted_buf.element_size()

            force_load_stat = f" Force pre-loaded {len(self.backup)} weights: {self.model.model_loaded_weight_memory // 1024} KB." if len(self.backup) > 0 else ""
            logging.info(f"Model {self.model.__class__.__name__} prepared for dynamic VRAM loading. {allocated_size // (1024 ** 2)}MB Staged. {num_patches} patches attached.{force_load_stat}")

            self.model.device = device_to
            self.model.current_weight_patches_uuid = self.patches_uuid

            for callback in self.get_all_callbacks(CallbacksMP.ON_LOAD):
                #These are all super dangerous. Who knows what the custom nodes actually do here...
                callback(self, device_to, lowvram_model_memory, force_patch_weights, full_load)

            self.apply_hooks(self.forced_hooks, force_apply=True)