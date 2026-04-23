def apply_color_transfer(source, target):
    """
    Apply color transfer using LAB color space. Handles potential division by zero and ensures output is uint8.
    """
    # Input validation
    if source is None or target is None or source.size == 0 or target.size == 0:
        # print("Warning: Invalid input to apply_color_transfer.")
        return source # Return original source if invalid input

    # Ensure images are 3-channel BGR uint8
    if len(source.shape) != 3 or source.shape[2] != 3 or source.dtype != np.uint8:
        # print("Warning: Source image for color transfer is not uint8 BGR.")
        # Attempt conversion if possible, otherwise return original
        try:
            if len(source.shape) == 2: # Grayscale
                source = cv2.cvtColor(source, cv2.COLOR_GRAY2BGR)
            source = np.clip(source, 0, 255).astype(np.uint8)
            if len(source.shape)!= 3 or source.shape[2]!= 3: raise ValueError("Conversion failed")
        except Exception:
            return source
    if len(target.shape) != 3 or target.shape[2] != 3 or target.dtype != np.uint8:
        # print("Warning: Target image for color transfer is not uint8 BGR.")
        try:
            if len(target.shape) == 2: # Grayscale
                target = cv2.cvtColor(target, cv2.COLOR_GRAY2BGR)
            target = np.clip(target, 0, 255).astype(np.uint8)
            if len(target.shape)!= 3 or target.shape[2]!= 3: raise ValueError("Conversion failed")
        except Exception:
             return source # Return original source if target invalid

    result_bgr = source # Default to original source in case of errors

    try:
        # Convert to float32 [0, 1] range for LAB conversion
        source_float = source.astype(np.float32) / 255.0
        target_float = target.astype(np.float32) / 255.0

        source_lab = cv2.cvtColor(source_float, cv2.COLOR_BGR2LAB)
        target_lab = cv2.cvtColor(target_float, cv2.COLOR_BGR2LAB)

        # Compute statistics
        source_mean, source_std = cv2.meanStdDev(source_lab)
        target_mean, target_std = cv2.meanStdDev(target_lab)

        # Reshape for broadcasting
        source_mean = source_mean.reshape((1, 1, 3))
        source_std = source_std.reshape((1, 1, 3))
        target_mean = target_mean.reshape((1, 1, 3))
        target_std = target_std.reshape((1, 1, 3))

        # Avoid division by zero or very small std deviations (add epsilon)
        epsilon = 1e-6
        source_std = np.maximum(source_std, epsilon)
        # target_std = np.maximum(target_std, epsilon) # Target std can be small

        # Perform color transfer in LAB space
        result_lab = (source_lab - source_mean) * (target_std / source_std) + target_mean

        # --- No explicit clipping needed in LAB space typically ---
        # Clipping is handled implicitly by the conversion back to BGR and then to uint8

        # Convert back to BGR float [0, 1]
        result_bgr_float = cv2.cvtColor(result_lab, cv2.COLOR_LAB2BGR)

        # Clip final BGR values to [0, 1] range before scaling to [0, 255]
        result_bgr_float = np.clip(result_bgr_float, 0.0, 1.0)

        # Convert back to uint8 [0, 255]
        result_bgr = (result_bgr_float * 255.0).astype("uint8")

    except cv2.error as e:
         # print(f"OpenCV error during color transfer: {e}. Returning original source.") # Optional debug
         return source # Return original source if conversion fails
    except Exception as e:
         # print(f"Unexpected color transfer error: {e}. Returning original source.") # Optional debug
         # import traceback
         # traceback.print_exc()
         return source

    return result_bgr