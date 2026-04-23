def static_call(x, negative_slope=0.0, max_value=None, threshold=0.0):
        x = backend.convert_to_tensor(x)
        if negative_slope != 0.0:
            if max_value is None and threshold == 0:
                return backend.nn.leaky_relu(x, negative_slope=negative_slope)

            if threshold != 0:
                negative_part = backend.nn.relu(-x + threshold)
            else:
                negative_part = backend.nn.relu(-x)
        else:
            negative_part = 1

        clip_max = max_value is not None
        if threshold != 0:
            # computes x for x > threshold else 0
            threshold = ops.cast(threshold, dtype=x.dtype)
            x = x * backend.cast(
                backend.numpy.greater(x, threshold), dtype=x.dtype
            )
        elif max_value == 6:
            # if no threshold, then can use nn.relu6 native op for performance
            x = backend.nn.relu6(x)
            clip_max = False
        else:
            x = backend.nn.relu(x)

        if clip_max:
            min_value = ops.cast(0.0, dtype=x.dtype)
            max_value = ops.cast(max_value, dtype=x.dtype)
            x = backend.numpy.clip(x, min_value, max_value)

        if negative_slope != 0.0:
            x -= negative_slope * negative_part
        return x