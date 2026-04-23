def get_vision_features(self, frame_idx: int) -> dict | None:
        """Get cached vision features, automatically moved to inference device."""
        if frame_idx not in self._vision_features:
            return None

        cached = self._vision_features[frame_idx]
        moved = {}
        for key, value in cached.items():
            if isinstance(value, torch.Tensor):
                moved[key] = value.to(self.inference_device, non_blocking=True)
            elif isinstance(value, (list, tuple)) and value and isinstance(value[0], torch.Tensor):
                moved[key] = [v.to(self.inference_device, non_blocking=True) for v in value]
            else:
                moved[key] = value
        return moved