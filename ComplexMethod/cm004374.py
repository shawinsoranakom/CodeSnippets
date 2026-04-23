def _left_pad_inputs_with_attention_mask(self, model_inputs: list[dict], return_attention_mask: bool):
        max_length_input_ids = max(entry["input_ids"].shape[1] for entry in model_inputs)
        max_length_image_patch_indices = max(entry["image_patches_indices"].shape[1] for entry in model_inputs)

        batched_inputs = {"input_ids": [], "image_patches": [], "image_patches_indices": [], "attention_mask": []}

        for entry in model_inputs:
            for key, tensor in entry.items():
                if key == "input_ids":
                    num_padding_tokens = max_length_input_ids - tensor.shape[1]
                    padded_input_ids = torch.cat(
                        [
                            torch.full((tensor.shape[0], num_padding_tokens), self.pad_token_id, dtype=torch.long),
                            tensor,
                        ],
                        dim=1,
                    )
                    batched_inputs[key].append(padded_input_ids)

                    attention_mask = torch.cat(
                        [torch.zeros(tensor.shape[0], num_padding_tokens, dtype=torch.long), torch.ones_like(tensor)],
                        dim=1,
                    )
                    batched_inputs["attention_mask"].append(attention_mask)

                elif key == "image_patches":
                    # For image_patches, we don't pad but just append them to the list.
                    batched_inputs[key].append(tensor)

                else:  # for image_patches_indices
                    num_padding_indices = max_length_image_patch_indices - tensor.shape[1]
                    padded_indices = torch.cat(
                        [
                            torch.full(
                                (tensor.shape[0], num_padding_indices), self.dummy_image_index, dtype=torch.long
                            ),
                            tensor,
                        ],
                        dim=1,
                    )
                    batched_inputs[key].append(padded_indices)
        batched_keys = ["input_ids", "image_patches_indices"]
        if return_attention_mask:
            batched_keys.append("attention_mask")
        for key in batched_keys:
            batched_inputs[key] = torch.cat(batched_inputs[key], dim=0)

        # Cast images to tensor as well, if only one image passed and no padding needed
        # NOTE: vLLM expects all processor outputs to be a tensor
        if len(batched_inputs["image_patches"]) == 1:
            batched_inputs["image_patches"] = torch.cat(batched_inputs["image_patches"], dim=0)

        return batched_inputs