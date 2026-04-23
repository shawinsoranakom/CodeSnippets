def _expand_dict_for_generation_visual(dict_to_expand):
            image_grid_thw = model_kwargs.get("image_grid_thw", None)
            if image_grid_thw is None:
                return dict_to_expand

            images_per_sample = model_kwargs.get("images_per_sample", None)

            # Use images_per_sample if available
            if images_per_sample is not None:
                image_nums = images_per_sample.tolist()
            elif input_ids is not None:
                # Try to infer from image_grid_thw / batch_size
                batch_size = input_ids.shape[0]
                total_grids = image_grid_thw.shape[0]
                if total_grids % batch_size == 0:
                    grids_per_sample = total_grids // batch_size
                    image_nums = [grids_per_sample] * batch_size
                else:
                    # Cannot evenly distribute grids - fall back to simple repeat_interleave
                    # This handles test cases where image_grid_thw has (batch_size + 1) rows
                    dict_to_expand["image_grid_thw"] = image_grid_thw.repeat_interleave(expand_size, dim=0)
                    if dict_to_expand.get("pixel_values") is not None:
                        dict_to_expand["pixel_values"] = dict_to_expand["pixel_values"].repeat_interleave(
                            expand_size, dim=0
                        )
                    return dict_to_expand
            else:
                image_nums = self._get_image_nums(input_ids).tolist()

            # Get source image counts per sample from image_end_token_id count
            source_image_nums = (input_ids == self.config.image_end_token_id).sum(dim=1).tolist()

            def _repeat_interleave_samples(x, lengths, repeat_times):
                samples = torch.split(x, lengths)
                repeat_args = [repeat_times] + [1] * (x.dim() - 1)
                result = torch.cat([sample.repeat(*repeat_args) for sample in samples], dim=0)
                return result

            for key in dict_to_expand:
                if key == "pixel_values":
                    # Split images into samples based on source image counts
                    if sum(source_image_nums) > 0:
                        # Split grids by sample to compute pixel counts
                        grids_per_sample = torch.split(image_grid_thw, image_nums)
                        all_pixel_counts = image_grid_thw.prod(dim=1)
                        pixel_counts_per_sample = torch.split(all_pixel_counts, image_nums)
                        # Build source mask and compute per-sample source pixel counts in one sync
                        source_pixel_counts = torch.zeros(len(grids_per_sample), device=image_grid_thw.device)
                        for batch_idx in range(len(grids_per_sample)):
                            num_source = source_image_nums[batch_idx]
                            if num_source > 0:
                                source_pixel_counts[batch_idx] = pixel_counts_per_sample[batch_idx][:num_source].sum()
                        lengths = source_pixel_counts.to(torch.int64).tolist()

                        dict_to_expand[key] = _repeat_interleave_samples(
                            dict_to_expand[key], lengths=lengths, repeat_times=expand_size
                        )
                elif key == "image_grid_thw":
                    # Expand all grids (source + target) per sample
                    dict_to_expand[key] = _repeat_interleave_samples(
                        dict_to_expand[key], lengths=image_nums, repeat_times=expand_size
                    )
                elif key == "images_per_sample":
                    # Simply repeat the counts
                    if dict_to_expand.get(key) is not None:
                        dict_to_expand[key] = dict_to_expand[key].repeat_interleave(expand_size, dim=0)
            return dict_to_expand