def vae_encode_crop_pixels(self, pixels):
        if self.crop_input:
            downscale_ratio = self.spacial_compression_encode()

            dims = pixels.shape[1:-1]
            for d in range(len(dims)):
                x = (dims[d] // downscale_ratio) * downscale_ratio
                x_offset = (dims[d] % downscale_ratio) // 2
                if x != dims[d]:
                    pixels = pixels.narrow(d + 1, x_offset, x)

        if pixels.shape[-1] > self.output_channels:
            pixels = pixels[..., :self.output_channels]
        elif pixels.shape[-1] < self.output_channels:
            if self.pad_channel_value is not None:
                if isinstance(self.pad_channel_value, str):
                    mode = self.pad_channel_value
                    value = None
                else:
                    mode = "constant"
                    value = self.pad_channel_value

                pixels = torch.nn.functional.pad(pixels, (0, self.output_channels - pixels.shape[-1]), mode=mode, value=value)
        return pixels