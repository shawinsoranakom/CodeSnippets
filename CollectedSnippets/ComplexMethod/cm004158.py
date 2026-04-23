def forward(
        self,
        pixel_values: torch.FloatTensor | None = None,
        labels: torch.LongTensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple | ImageSuperResolutionOutput:
        r"""
        Example:
         ```python
         >>> import torch
         >>> import numpy as np
         >>> from PIL import Image
         >>> import httpx
        >>> from io import BytesIO

         >>> from transformers import AutoImageProcessor, Swin2SRForImageSuperResolution

         >>> processor = AutoImageProcessor.from_pretrained("caidas/swin2SR-classical-sr-x2-64")
         >>> model = Swin2SRForImageSuperResolution.from_pretrained("caidas/swin2SR-classical-sr-x2-64")

         >>> url = "https://huggingface.co/spaces/jjourney1125/swin2sr/resolve/main/samples/butterfly.jpg"
         >>> with httpx.stream("GET", url) as response:
         ...     image = Image.open(BytesIO(response.read()))
         >>> # prepare image for the model
         >>> inputs = processor(image, return_tensors="pt")

         >>> # forward pass
         >>> with torch.no_grad():
         ...     outputs = model(**inputs)

         >>> output = outputs.reconstruction.data.squeeze().float().cpu().clamp_(0, 1).numpy()
         >>> output = np.moveaxis(output, source=0, destination=-1)
         >>> output = (output * 255.0).round().astype(np.uint8)  # float32 to uint8
         >>> # you can visualize `output` with `Image.fromarray`
         ```"""
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        loss = None
        if labels is not None:
            raise NotImplementedError("Training is not supported at the moment")

        height, width = pixel_values.shape[2:]

        if self.config.upsampler == "pixelshuffle_aux":
            bicubic = nn.functional.interpolate(
                pixel_values,
                size=(height * self.upscale, width * self.upscale),
                mode="bicubic",
                align_corners=False,
            )

        outputs = self.swin2sr(
            pixel_values,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        sequence_output = outputs[0]

        if self.upsampler in ["pixelshuffle", "pixelshuffledirect", "nearest+conv"]:
            reconstruction = self.upsample(sequence_output)
        elif self.upsampler == "pixelshuffle_aux":
            reconstruction, aux = self.upsample(sequence_output, bicubic, height, width)
            aux = aux / self.swin2sr.img_range + self.swin2sr.mean
        else:
            reconstruction = pixel_values + self.final_convolution(sequence_output)

        reconstruction = reconstruction / self.swin2sr.img_range + self.swin2sr.mean
        reconstruction = reconstruction[:, :, : height * self.upscale, : width * self.upscale]

        if not return_dict:
            output = (reconstruction,) + outputs[1:]
            return ((loss,) + output) if loss is not None else output

        return ImageSuperResolutionOutput(
            loss=loss,
            reconstruction=reconstruction,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
        )