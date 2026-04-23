def encode_from_tokens_scheduled(self, tokens, unprojected=False, add_dict: dict[str]={}, show_pbar=True):
        all_cond_pooled: list[tuple[torch.Tensor, dict[str]]] = []
        all_hooks = self.patcher.forced_hooks
        if all_hooks is None or not self.use_clip_schedule:
            # if no hooks or shouldn't use clip schedule, do unscheduled encode_from_tokens and perform add_dict
            return_pooled = "unprojected" if unprojected else True
            pooled_dict = self.encode_from_tokens(tokens, return_pooled=return_pooled, return_dict=True)
            cond = pooled_dict.pop("cond")
            # add/update any keys with the provided add_dict
            pooled_dict.update(add_dict)
            all_cond_pooled.append([cond, pooled_dict])
        else:
            scheduled_keyframes = all_hooks.get_hooks_for_clip_schedule()

            self.cond_stage_model.reset_clip_options()
            if self.layer_idx is not None:
                self.cond_stage_model.set_clip_options({"layer": self.layer_idx})
            if unprojected:
                self.cond_stage_model.set_clip_options({"projected_pooled": False})

            self.load_model(tokens)
            self.cond_stage_model.set_clip_options({"execution_device": self.patcher.load_device})
            all_hooks.reset()
            self.patcher.patch_hooks(None)
            if show_pbar:
                pbar = ProgressBar(len(scheduled_keyframes))

            for scheduled_opts in scheduled_keyframes:
                t_range = scheduled_opts[0]
                # don't bother encoding any conds outside of start_percent and end_percent bounds
                if "start_percent" in add_dict:
                    if t_range[1] < add_dict["start_percent"]:
                        continue
                if "end_percent" in add_dict:
                    if t_range[0] > add_dict["end_percent"]:
                        continue
                hooks_keyframes = scheduled_opts[1]
                for hook, keyframe in hooks_keyframes:
                    hook.hook_keyframe._current_keyframe = keyframe
                # apply appropriate hooks with values that match new hook_keyframe
                self.patcher.patch_hooks(all_hooks)
                # perform encoding as normal
                o = self.cond_stage_model.encode_token_weights(tokens)
                cond, pooled = o[:2]
                pooled_dict = {"pooled_output": pooled}
                # add clip_start_percent and clip_end_percent in pooled
                pooled_dict["clip_start_percent"] = t_range[0]
                pooled_dict["clip_end_percent"] = t_range[1]
                # add/update any keys with the provided add_dict
                pooled_dict.update(add_dict)
                # add hooks stored on clip
                self.add_hooks_to_dict(pooled_dict)
                all_cond_pooled.append([cond, pooled_dict])
                if show_pbar:
                    pbar.update(1)
                model_management.throw_exception_if_processing_interrupted()
            all_hooks.reset()
        return all_cond_pooled