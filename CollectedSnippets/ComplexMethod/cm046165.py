def _add_output_per_object(
        self, frame_idx, current_out, storage_key, inference_state: dict[str, Any] | None = None
    ):
        """Split a multi-object output into per-object output slices and add them into Output_Dict_Per_Obj.

        The resulting slices share the same tensor storage.

        Args:
            frame_idx (int): The index of the current frame.
            current_out (dict): The current output dictionary containing multi-object outputs.
            storage_key (str): The key used to store the output in the per-object output dictionary.
            inference_state (dict[str, Any], optional): The current inference state. If None, uses the instance's
                inference state.
        """
        inference_state = inference_state or self.inference_state
        maskmem_features = current_out["maskmem_features"]
        assert maskmem_features is None or isinstance(maskmem_features, torch.Tensor)

        maskmem_pos_enc = current_out["maskmem_pos_enc"]
        assert maskmem_pos_enc is None or isinstance(maskmem_pos_enc, list)

        for obj_idx, obj_output_dict in inference_state["output_dict_per_obj"].items():
            obj_slice = slice(obj_idx, obj_idx + 1)
            obj_out = {
                "maskmem_features": None,
                "maskmem_pos_enc": None,
                "pred_masks": current_out["pred_masks"][obj_slice],
                "obj_ptr": current_out["obj_ptr"][obj_slice],
            }
            if maskmem_features is not None:
                obj_out["maskmem_features"] = maskmem_features[obj_slice]
            if maskmem_pos_enc is not None:
                obj_out["maskmem_pos_enc"] = [x[obj_slice] for x in maskmem_pos_enc]
            obj_output_dict[storage_key][frame_idx] = obj_out