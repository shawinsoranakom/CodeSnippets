def _load_from_state_dict(self, state_dict, prefix, local_metadata,
                                    strict, missing_keys, unexpected_keys, error_msgs):

                device = self.factory_kwargs["device"]
                layer_name = prefix.rstrip('.')
                weight_key = f"{prefix}weight"
                weight = state_dict.pop(weight_key, None)
                if weight is None:
                    logging.warning(f"Missing weight for layer {layer_name}")
                    self.weight = None
                    return

                manually_loaded_keys = [weight_key]

                layer_conf = state_dict.pop(f"{prefix}comfy_quant", None)
                if layer_conf is not None:
                    layer_conf = json.loads(layer_conf.numpy().tobytes())

                if layer_conf is None:
                    self.weight = torch.nn.Parameter(weight.to(device=device, dtype=MixedPrecisionOps._compute_dtype), requires_grad=False)
                else:
                    self.quant_format = layer_conf.get("format", None)
                    self._full_precision_mm_config = layer_conf.get("full_precision_matrix_mult", False)
                    if not self._full_precision_mm:
                        self._full_precision_mm = self._full_precision_mm_config

                    if self.quant_format in MixedPrecisionOps._disabled:
                        self._full_precision_mm = True

                    if self.quant_format is None:
                        raise ValueError(f"Unknown quantization format for layer {layer_name}")

                    qconfig = QUANT_ALGOS[self.quant_format]
                    self.layout_type = qconfig["comfy_tensor_layout"]
                    layout_cls = get_layout_class(self.layout_type)

                    # Load format-specific parameters
                    if self.quant_format in ["float8_e4m3fn", "float8_e5m2"]:
                        # FP8: single tensor scale
                        scale = self._load_scale_param(state_dict, prefix, "weight_scale", device, manually_loaded_keys)

                        params = layout_cls.Params(
                            scale=scale,
                            orig_dtype=MixedPrecisionOps._compute_dtype,
                            orig_shape=(self.out_features, self.in_features),
                        )

                    elif self.quant_format == "mxfp8":
                        # MXFP8: E8M0 block scales stored as uint8 in safetensors
                        block_scale = self._load_scale_param(state_dict, prefix, "weight_scale", device, manually_loaded_keys,
                                                             dtype=torch.uint8)

                        if block_scale is None:
                            raise ValueError(f"Missing MXFP8 block scales for layer {layer_name}")

                        block_scale = block_scale.view(torch.float8_e8m0fnu)

                        params = layout_cls.Params(
                            scale=block_scale,
                            orig_dtype=MixedPrecisionOps._compute_dtype,
                            orig_shape=(self.out_features, self.in_features),
                        )

                    elif self.quant_format == "nvfp4":
                        # NVFP4: tensor_scale (weight_scale_2) + block_scale (weight_scale)
                        tensor_scale = self._load_scale_param(state_dict, prefix, "weight_scale_2", device, manually_loaded_keys)
                        block_scale = self._load_scale_param(state_dict, prefix, "weight_scale", device, manually_loaded_keys,
                                                             dtype=torch.float8_e4m3fn)

                        if tensor_scale is None or block_scale is None:
                            raise ValueError(f"Missing NVFP4 scales for layer {layer_name}")

                        params = layout_cls.Params(
                            scale=tensor_scale,
                            block_scale=block_scale,
                            orig_dtype=MixedPrecisionOps._compute_dtype,
                            orig_shape=(self.out_features, self.in_features),
                        )
                    else:
                        raise ValueError(f"Unsupported quantization format: {self.quant_format}")

                    self.weight = torch.nn.Parameter(
                        QuantizedTensor(weight.to(device=device, dtype=qconfig["storage_t"]), self.layout_type, params),
                        requires_grad=False
                    )

                    for param_name in qconfig["parameters"]:
                        if param_name in {"weight_scale", "weight_scale_2"}:
                            continue  # Already handled above

                        param_key = f"{prefix}{param_name}"
                        _v = state_dict.pop(param_key, None)
                        if _v is None:
                            continue
                        self.register_parameter(param_name, torch.nn.Parameter(_v.to(device=device), requires_grad=False))
                        manually_loaded_keys.append(param_key)

                super()._load_from_state_dict(state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs)

                for key in manually_loaded_keys:
                    if key in missing_keys:
                        missing_keys.remove(key)