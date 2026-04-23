def clear_all_points_in_frame(self, inference_state, frame_idx, obj_id):
        """Remove all input points or mask in a specific frame for a given object."""
        obj_idx = self._obj_id_to_idx(obj_id, inference_state)

        # Clear the conditioning information on the given frame
        inference_state["point_inputs_per_obj"][obj_idx].pop(frame_idx, None)
        inference_state["mask_inputs_per_obj"][obj_idx].pop(frame_idx, None)

        temp_output_dict_per_obj = inference_state["temp_output_dict_per_obj"]
        temp_output_dict_per_obj[obj_idx]["cond_frame_outputs"].pop(frame_idx, None)
        temp_output_dict_per_obj[obj_idx]["non_cond_frame_outputs"].pop(frame_idx, None)

        # Check and see if there are still any inputs left on this frame
        batch_size = len(inference_state["obj_idx_to_id"])
        frame_has_input = False
        for obj_idx2 in range(batch_size):
            if frame_idx in inference_state["point_inputs_per_obj"][obj_idx2]:
                frame_has_input = True
                break
            if frame_idx in inference_state["mask_inputs_per_obj"][obj_idx2]:
                frame_has_input = True
                break

        # If this frame has no remaining inputs for any objects, we further clear its
        # conditioning frame status
        if not frame_has_input:
            output_dict = inference_state["output_dict"]
            consolidated_frame_inds = inference_state["consolidated_frame_inds"]
            consolidated_frame_inds["cond_frame_outputs"].discard(frame_idx)
            consolidated_frame_inds["non_cond_frame_outputs"].discard(frame_idx)
            # Remove the frame's conditioning output (possibly downgrading it to non-conditioning)
            out = output_dict["cond_frame_outputs"].pop(frame_idx, None)
            if out is not None:
                # The frame is not a conditioning frame anymore since it's not receiving inputs,
                # so we "downgrade" its output (if exists) to a non-conditioning frame output.
                output_dict["non_cond_frame_outputs"][frame_idx] = out
                inference_state["frames_already_tracked"].pop(frame_idx, None)
            # Similarly, do it for the sliced output on each object.
            for obj_idx2 in range(batch_size):
                obj_output_dict = inference_state["output_dict_per_obj"][obj_idx2]
                obj_out = obj_output_dict["cond_frame_outputs"].pop(frame_idx, None)
                if obj_out is not None:
                    obj_output_dict["non_cond_frame_outputs"][frame_idx] = obj_out

            # If all the conditioning frames have been removed, we also clear the tracking outputs
            if len(output_dict["cond_frame_outputs"]) == 0:
                self._reset_tracking_results(inference_state)