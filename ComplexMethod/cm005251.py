def cache_vision_features(self, frame_idx: int, features: dict):
        """Cache vision features with automatic device management."""
        cached = {}
        if len(self._vision_features) >= self.max_vision_features_cache_size:
            # remove the oldest frame
            self._vision_features.pop(min(self._vision_features.keys()))

        for key, value in features.items():
            if isinstance(value, torch.Tensor):
                cached[key] = value.to(self.inference_state_device, non_blocking=True)
            elif isinstance(value, (list, tuple)) and value and isinstance(value[0], torch.Tensor):
                cached[key] = [v.to(self.inference_state_device, non_blocking=True) for v in value]
            else:
                cached[key] = value
        self._vision_features[frame_idx] = cached