def get_mask(self, name: str | None = None, layer: nn.Module | None = None):
        """
        Returns mask associated to the layer.

        The mask is
            - a torch tensor is features for that layer is None.
            - a list of torch tensors for each feature, otherwise

        Note::
            The shape of the mask is unknown until model.forward() is applied.
            Hence, if get_mask() is called before model.forward(), an
            error will be raised.
        """
        if name is None and layer is None:
            raise AssertionError("Need at least name or layer obj to retrieve mask")

        if name is None:
            if layer is None:
                raise AssertionError("layer must be provided when name is None")
            name = module_to_fqn(self.model, layer)
            if name is None:
                raise AssertionError("layer not found in the specified model")

        if name not in self.state:
            raise ValueError("Error: layer with the given name not found")

        mask = self.state[name].get("mask", None)

        if mask is None:
            raise ValueError(
                "Error: shape unknown, call layer() routine at least once to infer mask"
            )
        return mask