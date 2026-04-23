def __call__(self, features: list[dict[str, Any]]) -> dict[str, "torch.Tensor"]:
        batch_pixel_values = [feature.pop("pixel_values") for feature in features]
        batch_pixel_values_videos = [feature.pop("pixel_values_videos") for feature in features]
        batch_image_grid_thw = [feature.pop("image_grid_thw") for feature in features]
        batch_video_grid_thw = [feature.pop("video_grid_thw") for feature in features]

        batch: dict[str, torch.Tensor] = super().__call__(features)

        batch["pixel_values"] = torch.cat(batch_pixel_values, dim=0)
        batch["pixel_values_videos"] = torch.cat(batch_pixel_values_videos, dim=0)
        batch["image_grid_thw"] = torch.cat(batch_image_grid_thw, dim=0)
        batch["video_grid_thw"] = torch.cat(batch_video_grid_thw, dim=0)

        if self.get_rope_func is not None:
            rope_index_kwargs = {
                "input_ids": batch["input_ids"],
                "image_grid_thw": batch["image_grid_thw"],
                "video_grid_thw": batch["video_grid_thw"],
                "attention_mask": (batch["attention_mask"] >= 1).float(),
            }
            batch["position_ids"], batch["rope_deltas"] = self.get_rope_func(**rope_index_kwargs)

        if "position_ids" not in batch or batch["position_ids"].dim() != 3:
            raise ValueError("Qwen2VL requires 3D position ids for mrope.")

        return batch