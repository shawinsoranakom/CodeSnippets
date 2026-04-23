def forward(self, input, *args, **kwargs):
                run_every_op()

                input_shape = input.shape
                reshaped_3d = False
                #If cast needs to apply lora, it should be done in the compute dtype
                compute_dtype = input.dtype

                _use_quantized = (
                    getattr(self, 'layout_type', None) is not None and
                    not isinstance(input, QuantizedTensor) and not self._full_precision_mm and
                    not getattr(self, 'comfy_force_cast_weights', False) and
                    len(self.weight_function) == 0 and len(self.bias_function) == 0
                )

                # Training path: quantized forward with compute_dtype backward via autograd function
                if (input.requires_grad and _use_quantized):

                    weight, bias, offload_stream = cast_bias_weight(
                        self,
                        input,
                        offloadable=True,
                        compute_dtype=compute_dtype,
                        want_requant=True
                    )

                    scale = getattr(self, 'input_scale', None)
                    if scale is not None:
                        scale = comfy.model_management.cast_to_device(scale, input.device, None)

                    output = QuantLinearFunc.apply(
                        input, weight, bias, self.layout_type, scale, compute_dtype
                    )

                    uncast_bias_weight(self, weight, bias, offload_stream)
                    return output

                # Inference path (unchanged)
                if _use_quantized:

                    # Reshape 3D tensors to 2D for quantization (needed for NVFP4 and others)
                    input_reshaped = input.reshape(-1, input_shape[2]) if input.ndim == 3 else input

                    # Fall back to non-quantized for non-2D tensors
                    if input_reshaped.ndim == 2:
                        reshaped_3d = input.ndim == 3
                        # dtype is now implicit in the layout class
                        scale = getattr(self, 'input_scale', None)
                        if scale is not None:
                            scale = comfy.model_management.cast_to_device(scale, input.device, None)
                        input = QuantizedTensor.from_float(input_reshaped, self.layout_type, scale=scale)

                output = self.forward_comfy_cast_weights(input, compute_dtype, want_requant=isinstance(input, QuantizedTensor))

                # Reshape output back to 3D if input was 3D
                if reshaped_3d:
                    output = output.reshape((input_shape[0], input_shape[1], self.weight.shape[0]))

                return output