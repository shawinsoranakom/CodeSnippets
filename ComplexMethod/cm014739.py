def test_upsamplingBiMode2d_consistency(
        self,
        device,
        memory_format,
        mode,
        antialias,
        align_corners,
        num_channels,
        output_size,
        check_as_unsqueezed_3d_tensor,
        non_contig,
        batch_size,
    ):
        # Check output value consistency between resized_input_uint8 and resized input_float
        if torch.device(device).type == "cuda":
            raise SkipTest("CUDA implementation is not yet supporting uint8")

        if mode == "lanczos":
            if not antialias:
                raise SkipTest("Lanczos mode requires antialias=True")
            if align_corners:
                raise SkipTest("Lanczos mode does not support align_corners=True")

        torch.manual_seed(0)

        # - input range is set to [30, 220] for bicubic and lanczos modes,
        #   because these kernels may create [intermediate] values outside of
        #   the [0, 255] range, which need to be clipped in uint8 path, but
        #   not in float path. This isn't an issue with bilinear kernel.
        input_range = (30, 220) if mode in ("bicubic", "lanczos") else (0, 256)
        input_ui8 = torch.randint(*input_range, size=(batch_size, num_channels, 400, 400), dtype=torch.uint8, device=device)
        input_ui8 = input_ui8.contiguous(memory_format=memory_format)

        if non_contig == "sliced":
            input_ui8 = input_ui8[:, :, 10:-10, 10:-10]
        elif non_contig == "restrided":
            input_ui8 = input_ui8[:, :, ::2, ::2]

        if batch_size == 1 and check_as_unsqueezed_3d_tensor:
            input_ui8 = input_ui8[0, ...]
            input_ui8 = input_ui8[None, ...]

        input_f32 = input_ui8.float()

        output_f32 = F.interpolate(
            input_f32, size=(output_size, output_size), mode=mode, align_corners=align_corners, antialias=antialias
        ).round().clip(0, 255)
        output_ui8 = F.interpolate(
            input_ui8, size=(output_size, output_size), mode=mode, align_corners=align_corners, antialias=antialias
        )

        if non_contig is False:
            self.assertTrue(input_ui8.is_contiguous(memory_format=memory_format))

        # FIXME if-clause shows the current behaviour which is definitely unexpected.
        # Ideally we want to fix it such that both the ui8 and f32 outputs are also channels_last
        # See for more details: https://github.com/pytorch/pytorch/pull/100373
        if batch_size == 1 and check_as_unsqueezed_3d_tensor and memory_format == torch.channels_last:
            self.assertTrue(output_ui8.is_contiguous())
            self.assertTrue(output_f32.is_contiguous())
        else:
            self.assertTrue(output_ui8.is_contiguous(memory_format=memory_format))
            self.assertTrue(output_f32.is_contiguous(memory_format=memory_format))

        if mode == "bilinear":
            torch.testing.assert_close(output_f32, output_ui8.float(), rtol=0, atol=1)
        else:
            # bicubic and lanczos
            diff = (output_f32 - output_ui8.float()).abs()
            self.assertLess(diff.max(), 15)

            threshold = 2
            percent = 3
            self.assertLess((diff > threshold).float().mean(), percent / 100)

            threshold = 5
            percent = 1
            self.assertLess((diff > threshold).float().mean(), percent / 100)

            self.assertLess(diff.mean(), 0.4)