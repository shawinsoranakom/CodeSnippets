def reduce_data(
        self,
        elems: list[MultiModalFieldElem],
        *,
        device: torch.types.Device = None,
        pin_memory: bool = False,
    ) -> NestedTensors:
        """
        Merge the data from multiple instances of
        [`MultiModalFieldElem`][vllm.multimodal.inputs.MultiModalFieldElem].

        This is the inverse of
        [`build_elems`][vllm.multimodal.inputs.BaseMultiModalField.build_elems].
        """
        field_types = [type(item.field) for item in elems]
        if len(set(field_types)) > 1:
            raise ValueError(f"Cannot merge different {field_types=}")

        if device is not None and self.keep_on_cpu:
            device = "cpu"
        if pin_memory and self.keep_on_cpu:
            pin_memory = False

        batch = [elem.data for elem in elems]
        out = self._reduce_data(batch, pin_memory=pin_memory)
        return _nested_tensors_h2d(out, device=device)