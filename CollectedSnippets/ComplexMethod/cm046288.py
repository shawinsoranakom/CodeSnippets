def forward(
        self,
        im: torch.Tensor,
        augment: bool = False,
        visualize: bool = False,
        embed: list | None = None,
        **kwargs: Any,
    ) -> torch.Tensor | list[torch.Tensor]:
        """Run inference on an AutoBackend model.

        Args:
            im (torch.Tensor): The image tensor to perform inference on.
            augment (bool): Whether to perform data augmentation during inference.
            visualize (bool): Whether to visualize the output predictions.
            embed (list, optional): A list of layer indices to return embeddings from.
            **kwargs (Any): Additional keyword arguments for model configuration.

        Returns:
            (torch.Tensor | list[torch.Tensor]): The raw output tensor(s) from the model.
        """
        if self.nhwc:
            im = im.permute(0, 2, 3, 1)  # torch BCHW to numpy BHWC shape(1,320,192,3)
        if self.backend.fp16 and im.dtype != torch.float16:
            im = im.half()

        # Build forward kwargs based on backend type
        forward_kwargs = {}
        if self.format == "pt":
            forward_kwargs = {"augment": augment, "visualize": visualize, "embed": embed, **kwargs}

        y = self.backend.forward(im, **forward_kwargs)

        if isinstance(y, (list, tuple)):
            if len(self.names) == 999 and (self.task == "segment" or len(y) == 2):  # segments and names not defined
                nc = y[0].shape[1] - y[1].shape[1] - 4  # y = (1, 116, 8400), (1, 32, 160, 160)
                self.names = {i: f"class{i}" for i in range(nc)}
            return self.from_numpy(y[0]) if len(y) == 1 else [self.from_numpy(x) for x in y]
        else:
            return self.from_numpy(y)