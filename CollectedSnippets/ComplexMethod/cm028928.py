def create_face_mask(face: Face, frame: Frame) -> np.ndarray:
    """Creates a feathered mask covering the whole face area based on landmarks."""
    if frame is None or not hasattr(frame, "shape") or len(frame.shape) < 2:
        return np.zeros((0, 0), dtype=np.uint8)

    mask = np.zeros(frame.shape[:2], dtype=np.uint8) # Start with uint8

    # Validate inputs
    if face is None or not hasattr(face, 'landmark_2d_106'):
        # print("Warning: Invalid face or frame for create_face_mask.")
        return mask # Return empty mask

    landmarks = face.landmark_2d_106
    if landmarks is None or not isinstance(landmarks, np.ndarray) or landmarks.shape[0] < 106:
        # print("Warning: Invalid or insufficient landmarks for face mask.")
        return mask # Return empty mask

    try: # Wrap main logic in try-except
        # Filter out non-finite landmark values
        if not np.all(np.isfinite(landmarks)):
            # print("Warning: Non-finite values detected in landmarks for face mask.")
            return mask

        landmarks_int = landmarks.astype(np.int32)

        # Use standard face outline landmarks (0-32)
        # Use standard face outline (0-32)
        face_outline = landmarks_int[0:33]

        # Estimate forehead points to ensure mask covers the whole face (including forehead)
        # This is critical for Poisson blending to work correctly on the forehead
        eyebrows = landmarks_int[33:43]
        if eyebrows.shape[0] > 0:
            chin = landmarks_int[16]
            eyebrow_center = np.mean(eyebrows, axis=0)

            # Vector from chin to eyebrows (upwards)
            up_vector = eyebrow_center - chin
            norm = np.linalg.norm(up_vector)
            if norm > 0:
                up_vector /= norm

                # Extend upwards by 1.0 of the chin-to-eyebrow distance (aggressive coverage)
                # This ensures the mask covers the entire forehead for proper blending
                forehead_offset = up_vector * (norm * 1.0)

                # Shift eyebrows up to create forehead points
                forehead_points = eyebrows + forehead_offset

                # Expand the top points slightly outwards to cover forehead corners
                # Calculate the center of the new top points
                top_center = np.mean(forehead_points, axis=0)

                # Expand outwards by 20%
                forehead_points = (forehead_points - top_center) * 1.2 + top_center

                # Combine outline and forehead points
                face_outline = np.concatenate((face_outline, forehead_points.astype(np.int32)), axis=0)

        # Calculate convex hull of these points
        # Use try-except as convexHull can fail on degenerate input
        try:
             hull = cv2.convexHull(face_outline.astype(np.float32)) # Use float for accuracy
             if hull is None or len(hull) < 3:
                 # print("Warning: Convex hull calculation failed or returned too few points.")
                 # Fallback: use bounding box of landmarks? Or just return empty mask?
                 return mask

             # Draw the filled convex hull on the mask
             cv2.fillConvexPoly(mask, hull.astype(np.int32), 255)
        except Exception as hull_e:
             print(f"Error creating convex hull for face mask: {hull_e}")
             return mask # Return empty mask on error


        # Apply Gaussian blur to feather the mask edges (GPU-accelerated when available)
        blur_k_size = getattr(modules.globals, "face_mask_blur", 31) # Default 31
        blur_k_size = max(1, blur_k_size // 2 * 2 + 1) # Ensure odd and positive
        mask = gpu_gaussian_blur(mask, (blur_k_size, blur_k_size), 0)

        # --- Optional: Return float mask for apply_mouth_area ---
        # mask = mask.astype(float) / 255.0
        # ---

    except IndexError:
        # print("Warning: Landmark index out of bounds for face mask.") # Optional debug
        pass
    except Exception as e:
        print(f"Error creating face mask: {e}") # Print unexpected errors
        # import traceback
        # traceback.print_exc()
        pass

    return mask