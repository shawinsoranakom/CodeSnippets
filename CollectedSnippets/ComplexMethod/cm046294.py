def forward(self, im: torch.Tensor) -> list[torch.Tensor]:
        """Run NVIDIA TensorRT inference with dynamic shape handling.

        Args:
            im (torch.Tensor): Input image tensor in BCHW format on the CUDA device.

        Returns:
            (list[torch.Tensor]): Model predictions as a list of tensors on the CUDA device.
        """
        if self.dynamic and im.shape != self.bindings["images"].shape:
            if self.is_trt10:
                self.context.set_input_shape("images", im.shape)
                self.bindings["images"] = self.bindings["images"]._replace(shape=im.shape)
                for name in self.output_names:
                    self.bindings[name].data.resize_(tuple(self.context.get_tensor_shape(name)))
            else:
                i = self.model.get_binding_index("images")
                self.context.set_binding_shape(i, im.shape)
                self.bindings["images"] = self.bindings["images"]._replace(shape=im.shape)
                for name in self.output_names:
                    i = self.model.get_binding_index(name)
                    self.bindings[name].data.resize_(tuple(self.context.get_binding_shape(i)))

        s = self.bindings["images"].shape
        assert im.shape == s, f"input size {im.shape} {'>' if self.dynamic else 'not equal to'} max model size {s}"

        self.binding_addrs["images"] = int(im.data_ptr())
        self.context.execute_v2(list(self.binding_addrs.values()))
        return [self.bindings[x].data for x in sorted(self.output_names)]