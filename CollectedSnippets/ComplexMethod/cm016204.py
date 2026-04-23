def create_shader_params(
        self, variant_params: dict[str, Any] | None = None
    ) -> dict[str, str]:
        if variant_params is None:
            variant_params = {}
        shader_params = copy.deepcopy(self.env)
        for key, value in variant_params.items():
            shader_params[key] = value

        shader_dtype = shader_params.get("DTYPE", "float")

        if shader_dtype == "int":
            shader_params["FORMAT"] = self.env["INT_IMAGE_FORMAT"]
        elif shader_dtype == "uint":
            shader_params["FORMAT"] = self.env["UINT_IMAGE_FORMAT"]
        elif shader_dtype == "int32":
            shader_params["FORMAT"] = "rgba32i"
        elif shader_dtype == "uint32":
            shader_params["FORMAT"] = "rgba32ui"
        elif shader_dtype == "int8":
            shader_params["FORMAT"] = "rgba8i"
        elif shader_dtype == "uint8":
            shader_params["FORMAT"] = "rgba8ui"
        elif shader_dtype == "float32":
            shader_params["FORMAT"] = "rgba32f"
        # Assume float by default
        else:
            shader_params["FORMAT"] = self.env["FLOAT_IMAGE_FORMAT"]

        return shader_params