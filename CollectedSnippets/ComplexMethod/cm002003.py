def test_crop_to_patches_aspect_ratio(self):
        """Test that row/column ordering is correct when cropping non-square images to patches.

        This test verifies that patches can be stitched back to reconstruct the original image,
        which validates that the row/column ordering in get_optimal_tiled_canvas is correct.
        If row/column are swapped, the image would be resized to wrong dimensions and patches
        would not match the original content.
        """
        for image_processing_class in self.image_processing_classes.values():
            patch_size = 64
            image_processor = image_processing_class(
                do_resize=True,
                size={"height": patch_size, "width": patch_size},
                do_normalize=False,  # Disable normalization to preserve pixel values
                do_rescale=False,  # Disable rescaling to preserve pixel values
                crop_to_patches=True,
                min_patches=1,
                max_patches=6,  # Allow up to 6 patches to test asymmetric grids like 2x3
            )

            # Create a 2:3 aspect ratio image (2 rows x 3 columns of patches)
            # This asymmetric grid will fail if rows/columns are swapped
            num_rows, num_cols = 2, 3
            image_height = patch_size * num_rows  # 128
            image_width = patch_size * num_cols  # 192

            # Create image with unique color for each patch position
            test_image = Image.new("RGB", (image_width, image_height))
            for row in range(num_rows):
                for col in range(num_cols):
                    patch_idx = row * num_cols + col  # 0-5
                    color = (patch_idx * 40 + 20, 0, 0)  # Unique red values: 20, 60, 100, 140, 180, 220
                    for y in range(patch_size):
                        for x in range(patch_size):
                            test_image.putpixel(
                                (col * patch_size + x, row * patch_size + y),
                                color,
                            )

            # Process image
            result = image_processor(test_image, return_tensors="pt")
            patches = result.pixel_values
            num_patches_result = result.num_patches

            # Should produce 7 patches (6 grid patches + 1 thumbnail)
            self.assertEqual(num_patches_result.tolist(), [7])
            self.assertEqual(tuple(patches.shape), (7, 3, patch_size, patch_size))

            # Verify each patch has the correct color (excluding thumbnail which is last)
            # Patches should be ordered row by row: (0,0), (0,1), (0,2), (1,0), (1,1), (1,2)
            for patch_idx in range(6):
                expected_red = patch_idx * 40 + 20
                actual_red = patches[patch_idx, 0, 0, 0].item()  # Red channel, top-left pixel
                self.assertEqual(
                    actual_red,
                    expected_red,
                    f"Patch {patch_idx} has wrong color. Expected red={expected_red}, got {actual_red}. "
                    f"This indicates row/column ordering is incorrect.",
                )

            # Stitch patches back and verify against original
            stitched = torch.zeros(3, image_height, image_width)
            for patch_idx in range(6):
                row = patch_idx // num_cols
                col = patch_idx % num_cols
                stitched[
                    :,
                    row * patch_size : (row + 1) * patch_size,
                    col * patch_size : (col + 1) * patch_size,
                ] = patches[patch_idx]

            original_tensor = torch.tensor(np.array(test_image)).permute(2, 0, 1).float()
            self.assertTrue(
                torch.allclose(stitched, original_tensor),
                "Patches do not stitch back to original image - row/column ordering may be wrong",
            )