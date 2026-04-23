def _prune_non_cond_memory(self, frame_idx, inference_state=None):
        """Prune old non-conditioning frames to bound memory usage."""
        if not self.clear_non_cond_mem:
            return
        inference_state = inference_state or self.inference_state

        # Determine window size
        min_frame = frame_idx - self.model.num_maskmem * self.model.memory_temporal_stride_for_eval
        output_dict = inference_state["output_dict"]

        # Prune global non_cond_frame_outputs
        for f in [k for k in output_dict["non_cond_frame_outputs"] if k < min_frame]:
            output_dict["non_cond_frame_outputs"].pop(f, None)

        # Prune per-object non_cond_frame_outputs
        for obj_output_dict in inference_state.get("output_dict_per_obj", {}).values():
            for f in [k for k in obj_output_dict["non_cond_frame_outputs"] if k < min_frame]:
                obj_output_dict["non_cond_frame_outputs"].pop(f, None)