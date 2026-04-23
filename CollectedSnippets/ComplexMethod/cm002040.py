def test_batch_tiling(self):
        """Test that patches from different images don't get mixed when batch processing with tiling.

        This test verifies that when processing a batch of images with tiling enabled,
        patches from image 0 don't end up in image 1's output and vice versa.
        This was a bug caused by incorrect permute/reshape operations in crop_image_to_patches.
        """
        for use_thumbnail in [False, True]:
            with self.subTest(use_thumbnail=use_thumbnail):
                image_processing = self.image_processing_classes["torchvision"](
                    do_image_splitting=True,
                    use_thumbnail=use_thumbnail,
                    min_tiles=2,
                    max_tiles=4,
                    tile_size=512,
                )

                # Create two large images with completely different solid colors
                # Red image: RGB = (255, 0, 0)
                # Blue image: RGB = (0, 0, 255)
                red_image = Image.new("RGB", (1024, 1024), color=(255, 0, 0))
                blue_image = Image.new("RGB", (1024, 1024), color=(0, 0, 255))

                result = image_processing(
                    [[red_image], [blue_image]],
                    return_tensors="pt",
                    return_row_col_info=True,
                    do_rescale=False,  # Keep original pixel values for easier verification
                    do_normalize=False,
                )

                # Each 1024x1024 image should be split into 2x2 = 4 tiles
                red_tiles = result.image_rows[0].item() * result.image_cols[0].item()
                blue_tiles = result.image_rows[1].item() * result.image_cols[1].item()
                self.assertEqual(red_tiles, 4)
                self.assertEqual(blue_tiles, 4)

                # Calculate expected total patches
                # Without thumbnail: 4 + 4 = 8
                # With thumbnail: (4 + 1) + (4 + 1) = 10
                thumb_count = 1 if use_thumbnail else 0
                expected_total = (red_tiles + thumb_count) + (blue_tiles + thumb_count)
                self.assertEqual(result.pixel_values.shape[0], expected_total)

                pixel_values = result.pixel_values
                patch_size = image_processing.encoder_patch_size
                patches_per_image = red_tiles + thumb_count

                # Check red image patches (and thumbnail if enabled)
                # All should have high red, zero blue
                for i in range(patches_per_image):
                    first_patch = pixel_values[i][0].view(3, patch_size, patch_size)
                    red_mean = first_patch[0].float().mean().item()
                    blue_mean = first_patch[2].float().mean().item()
                    patch_type = "thumbnail" if use_thumbnail and i == red_tiles else f"patch {i}"
                    self.assertGreater(
                        red_mean,
                        blue_mean,
                        f"Red image {patch_type} has more blue than red - patches may be interleaved",
                    )

                # Check blue image patches (and thumbnail if enabled)
                # All should have high blue, zero red
                for i in range(patches_per_image, 2 * patches_per_image):
                    first_patch = pixel_values[i][0].view(3, patch_size, patch_size)
                    red_mean = first_patch[0].float().mean().item()
                    blue_mean = first_patch[2].float().mean().item()
                    local_idx = i - patches_per_image
                    patch_type = "thumbnail" if use_thumbnail and local_idx == blue_tiles else f"patch {local_idx}"
                    self.assertGreater(
                        blue_mean,
                        red_mean,
                        f"Blue image {patch_type} has more red than blue - patches may be interleaved",
                    )