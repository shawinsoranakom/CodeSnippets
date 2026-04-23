def clean_batch_sizes(self, frames):
        # Clean up batch sizes when its 0
        if len(frames) == 1:
            return frames
        batch_sizes = frames[0]["batch_size"].to_list()
        for frame in frames[1:]:
            frame_batch_sizes = frame["batch_size"].to_list()
            for idx, (batch_a, batch_b) in enumerate(
                zip(batch_sizes, frame_batch_sizes)
            ):
                if not (batch_a == batch_b or batch_a == 0 or batch_b == 0):
                    raise AssertionError(
                        f"batch size mismatch: a={batch_a}, b={batch_b}"
                    )
                batch_sizes[idx] = max(batch_a, batch_b)
        for frame in frames:
            frame["batch_size"] = batch_sizes
        return frames