def calculate_weight(
        self,
        weight,
        key,
        strength,
        strength_model,
        offset,
        function,
        intermediate_dtype=torch.float32,
        original_weight=None,
    ):
        v = self.weights
        w1 = v[0]
        w2 = v[1]
        w1_a = v[3]
        w1_b = v[4]
        w2_a = v[5]
        w2_b = v[6]
        t2 = v[7]
        dora_scale = v[8]
        dim = None

        if w1 is None:
            dim = w1_b.shape[0]
            w1 = torch.mm(
                comfy.model_management.cast_to_device(
                    w1_a, weight.device, intermediate_dtype
                ),
                comfy.model_management.cast_to_device(
                    w1_b, weight.device, intermediate_dtype
                ),
            )
        else:
            w1 = comfy.model_management.cast_to_device(
                w1, weight.device, intermediate_dtype
            )

        if w2 is None:
            dim = w2_b.shape[0]
            if t2 is None:
                w2 = torch.mm(
                    comfy.model_management.cast_to_device(
                        w2_a, weight.device, intermediate_dtype
                    ),
                    comfy.model_management.cast_to_device(
                        w2_b, weight.device, intermediate_dtype
                    ),
                )
            else:
                w2 = torch.einsum(
                    "i j k l, j r, i p -> p r k l",
                    comfy.model_management.cast_to_device(
                        t2, weight.device, intermediate_dtype
                    ),
                    comfy.model_management.cast_to_device(
                        w2_b, weight.device, intermediate_dtype
                    ),
                    comfy.model_management.cast_to_device(
                        w2_a, weight.device, intermediate_dtype
                    ),
                )
        else:
            w2 = comfy.model_management.cast_to_device(
                w2, weight.device, intermediate_dtype
            )

        if len(w2.shape) == 4:
            w1 = w1.unsqueeze(2).unsqueeze(2)
        if v[2] is not None and dim is not None:
            alpha = v[2] / dim
        else:
            alpha = 1.0

        try:
            lora_diff = torch.kron(w1, w2).reshape(weight.shape)
            if dora_scale is not None:
                weight = weight_decompose(
                    dora_scale,
                    weight,
                    lora_diff,
                    alpha,
                    strength,
                    intermediate_dtype,
                    function,
                )
            else:
                weight += function(((strength * alpha) * lora_diff).type(weight.dtype))
        except Exception as e:
            logging.error("ERROR {} {} {}".format(self.name, key, e))
        return weight