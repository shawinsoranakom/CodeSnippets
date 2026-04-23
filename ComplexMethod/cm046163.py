def _get_maskmem_pos_enc(self, out_maskmem_pos_enc, inference_state: dict[str, Any] | None = None):
        """Cache and manage the positional encoding for mask memory across frames and objects.

        This method optimizes storage by caching the positional encoding (`maskmem_pos_enc`) for mask memory, which is
        constant across frames and objects, thus reducing the amount of redundant information stored during an inference
        session. It checks if the positional encoding has already been cached; if not, it caches a slice of the provided
        encoding. If the batch size is greater than one, it expands the cached positional encoding to match the current
        batch size.

        Args:
            out_maskmem_pos_enc (list[torch.Tensor] | None): The positional encoding for mask memory. Should be a list
                of tensors or None.
            inference_state (dict[str, Any], optional): The current inference state. If None, uses the instance's
                inference state.

        Returns:
            (list[torch.Tensor]): The positional encoding for mask memory, either cached or expanded.

        Notes:
            - The method assumes that `out_maskmem_pos_enc` is a list of tensors or None.
            - Only a single object's slice is cached since the encoding is the same across objects.
            - The method checks if the positional encoding has already been cached in the session's constants.
            - If the batch size is greater than one, the cached encoding is expanded to fit the batch size.
        """
        inference_state = inference_state or self.inference_state
        model_constants = inference_state["constants"]
        # "out_maskmem_pos_enc" should be either a list of tensors or None
        if out_maskmem_pos_enc is not None:
            if "maskmem_pos_enc" not in model_constants:
                assert isinstance(out_maskmem_pos_enc, list)
                # only take the slice for one object, since it's same across objects
                maskmem_pos_enc = [x[:1].clone() for x in out_maskmem_pos_enc]
                model_constants["maskmem_pos_enc"] = maskmem_pos_enc
            else:
                maskmem_pos_enc = model_constants["maskmem_pos_enc"]
            # expand the cached maskmem_pos_enc to the actual batch size
            batch_size = out_maskmem_pos_enc[0].shape[0]
            if batch_size > 1:
                out_maskmem_pos_enc = [x.expand(batch_size, -1, -1, -1) for x in maskmem_pos_enc]
        return out_maskmem_pos_enc