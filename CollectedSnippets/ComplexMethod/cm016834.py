def __call__(self, kwargs):
        x = kwargs.get("x")
        img = kwargs.get("img")
        img_input = kwargs.get("img_input")
        txt = kwargs.get("txt")
        pe = kwargs.get("pe")
        vec = kwargs.get("vec")
        block_index = kwargs.get("block_index")
        block_type = kwargs.get("block_type", "")
        spacial_compression = self.vae.spacial_compression_encode()
        if self.encoded_image is None or self.encoded_image_size != (x.shape[-2] * spacial_compression, x.shape[-1] * spacial_compression):
            image_scaled = None
            if self.image is not None:
                image_scaled = comfy.utils.common_upscale(self.image.movedim(-1, 1), x.shape[-1] * spacial_compression, x.shape[-2] * spacial_compression, "area", "center").movedim(1, -1)
                self.encoded_image_size = (image_scaled.shape[-3], image_scaled.shape[-2])

            inpaint_scaled = None
            if self.inpaint_image is not None:
                inpaint_scaled = comfy.utils.common_upscale(self.inpaint_image.movedim(-1, 1), x.shape[-1] * spacial_compression, x.shape[-2] * spacial_compression, "area", "center").movedim(1, -1)
                self.encoded_image_size = (inpaint_scaled.shape[-3], inpaint_scaled.shape[-2])

            loaded_models = comfy.model_management.loaded_models(only_currently_used=True)
            self.encoded_image = self.encode_latent_cond(image_scaled, inpaint_scaled)
            comfy.model_management.load_models_gpu(loaded_models)

        cnet_blocks = self.model_patch.model.n_control_layers
        div = round(30 / cnet_blocks)

        cnet_index = (block_index // div)
        cnet_index_float = (block_index / div)

        kwargs.pop("img")  # we do ops in place
        kwargs.pop("txt")

        if cnet_index_float > (cnet_blocks - 1):
            self.temp_data = None
            return kwargs

        if self.temp_data is None or self.temp_data[0] > cnet_index:
            if block_type == "noise_refiner":
                self.temp_data = (-3, (None, self.model_patch.model(txt, self.encoded_image.to(img.dtype), pe, vec)))
            else:
                self.temp_data = (-1, (None, self.model_patch.model(txt, self.encoded_image.to(img.dtype), pe, vec)))

        if block_type == "noise_refiner":
            next_layer = self.temp_data[0] + 1
            self.temp_data = (next_layer, self.model_patch.model.forward_noise_refiner_block(block_index, self.temp_data[1][1], img_input[:, :self.temp_data[1][1].shape[1]], None, pe, vec))
            if self.temp_data[1][0] is not None:
                img[:, :self.temp_data[1][0].shape[1]] += (self.temp_data[1][0] * self.strength)
        else:
            while self.temp_data[0] < cnet_index and (self.temp_data[0] + 1) < cnet_blocks:
                next_layer = self.temp_data[0] + 1
                self.temp_data = (next_layer, self.model_patch.model.forward_control_block(next_layer, self.temp_data[1][1], img_input[:, :self.temp_data[1][1].shape[1]], None, pe, vec))

            if cnet_index_float == self.temp_data[0]:
                img[:, :self.temp_data[1][0].shape[1]] += (self.temp_data[1][0] * self.strength)
                if cnet_blocks == self.temp_data[0] + 1:
                    self.temp_data = None

        return kwargs