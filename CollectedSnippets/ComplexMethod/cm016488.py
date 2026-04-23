def get_resized_cond(self, cond_in: list[dict], x_in: torch.Tensor, window: IndexListContextWindow, device=None) -> list:
        if cond_in is None:
            return None
        # reuse or resize cond items to match context requirements
        resized_cond = []
        # if multiple conds, split based on primary region
        if self.split_conds_to_windows and len(cond_in) > 1:
            region = window.get_region_index(len(cond_in))
            logging.info(f"Splitting conds to windows; using region {region} for window {window.index_list[0]}-{window.index_list[-1]} with center ratio {window.center_ratio:.3f}")
            cond_in = [cond_in[region]]
        # cond object is a list containing a dict - outer list is irrelevant, so just loop through it
        for actual_cond in cond_in:
            resized_actual_cond = actual_cond.copy()
            # now we are in the inner dict - "pooled_output" is a tensor, "control" is a ControlBase object, "model_conds" is dictionary
            for key in actual_cond:
                try:
                    cond_item = actual_cond[key]
                    if isinstance(cond_item, torch.Tensor):
                        # check that tensor is the expected length - x.size(0)
                        if self.dim < cond_item.ndim and cond_item.size(self.dim) == x_in.size(self.dim):
                            # if so, it's subsetting time - tell controls the expected indeces so they can handle them
                            actual_cond_item = window.get_tensor(cond_item)
                            resized_actual_cond[key] = actual_cond_item.to(device)
                        else:
                            resized_actual_cond[key] = cond_item.to(device)
                    # look for control
                    elif key == "control":
                        resized_actual_cond[key] = self.prepare_control_objects(cond_item, device)
                    elif isinstance(cond_item, dict):
                        new_cond_item = cond_item.copy()
                        # when in dictionary, look for tensors and CONDCrossAttn [comfy/conds.py] (has cond attr that is a tensor)
                        for cond_key, cond_value in new_cond_item.items():
                            # Allow callbacks to handle custom conditioning items
                            handled = False
                            for callback in comfy.patcher_extension.get_all_callbacks(
                                IndexListCallbacks.RESIZE_COND_ITEM, self.callbacks
                            ):
                                result = callback(cond_key, cond_value, window, x_in, device, new_cond_item)
                                if result is not None:
                                    new_cond_item[cond_key] = result
                                    handled = True
                                    break
                            if not handled and self._model is not None:
                                result = self._model.resize_cond_for_context_window(
                                    cond_key, cond_value, window, x_in, device,
                                    retain_index_list=self.cond_retain_index_list)
                                if result is not None:
                                    new_cond_item[cond_key] = result
                                    handled = True
                            if handled:
                                continue
                            if isinstance(cond_value, torch.Tensor):
                                if (self.dim < cond_value.ndim and cond_value.size(self.dim) == x_in.size(self.dim)) or \
                                   (cond_value.ndim < self.dim and cond_value.size(0) == x_in.size(self.dim)):
                                    new_cond_item[cond_key] = window.get_tensor(cond_value, device)
                            # Handle audio_embed (temporal dim is 1)
                            elif cond_key == "audio_embed" and hasattr(cond_value, "cond") and isinstance(cond_value.cond, torch.Tensor):
                                audio_cond = cond_value.cond
                                if audio_cond.ndim > 1 and audio_cond.size(1) == x_in.size(self.dim):
                                    new_cond_item[cond_key] = cond_value._copy_with(window.get_tensor(audio_cond, device, dim=1))
                            # Handle vace_context (temporal dim is 3)
                            elif cond_key == "vace_context" and hasattr(cond_value, "cond") and isinstance(cond_value.cond, torch.Tensor):
                                vace_cond = cond_value.cond
                                if vace_cond.ndim >= 4 and vace_cond.size(3) == x_in.size(self.dim):
                                    sliced_vace = window.get_tensor(vace_cond, device, dim=3, retain_index_list=self.cond_retain_index_list)
                                    new_cond_item[cond_key] = cond_value._copy_with(sliced_vace)
                            # if has cond that is a Tensor, check if needs to be subset
                            elif hasattr(cond_value, "cond") and isinstance(cond_value.cond, torch.Tensor):
                                if  (self.dim < cond_value.cond.ndim and cond_value.cond.size(self.dim) == x_in.size(self.dim)) or \
                                    (cond_value.cond.ndim < self.dim and cond_value.cond.size(0) == x_in.size(self.dim)):
                                    new_cond_item[cond_key] = cond_value._copy_with(window.get_tensor(cond_value.cond, device, retain_index_list=self.cond_retain_index_list))
                            elif cond_key == "num_video_frames": # for SVD
                                new_cond_item[cond_key] = cond_value._copy_with(cond_value.cond)
                                new_cond_item[cond_key].cond = window.context_length
                        resized_actual_cond[key] = new_cond_item
                    else:
                        resized_actual_cond[key] = cond_item
                finally:
                    del cond_item  # just in case to prevent VRAM issues
            resized_cond.append(resized_actual_cond)
        return resized_cond