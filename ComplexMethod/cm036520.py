def __call__(
            self,
            text: str,
            images: Image | list[Image] = None,
            videos: npt.NDArray | list[npt.NDArray] = None,
            **kwargs,
        ):
            from vllm.transformers_utils.processors.internvl import (
                image_to_pixel_values_internvl,
                video_to_pixel_values_internvl,
            )

            IMG_START = "<img>"
            IMG_END = "</img>"
            IMG_CONTEXT = "<IMG_CONTEXT>"

            images = [images] if isinstance(images, Image) else images
            videos = [videos] if isinstance(videos, np.ndarray) else videos
            if images is not None:
                pixel_values_images = [
                    image_to_pixel_values_internvl(
                        image,
                        input_size=self.image_size,
                        min_num=self.min_num,
                        max_num=self.max_num,
                        use_thumbnail=self.use_thumbnail,
                    )
                    for image in images
                ]
                num_patches_images = [
                    pixel_value.shape[0] for pixel_value in pixel_values_images
                ]
            else:
                pixel_values_images, num_patches_images = [], []

            if videos is not None:
                pixel_values_videos = [
                    video_to_pixel_values_internvl(
                        video,
                        input_size=self.image_size,
                        min_num=1,
                        max_num=1,
                        use_thumbnail=False,
                    )
                    for video in videos
                ]
                num_patches_videos = [
                    pixel_value.shape[0] for pixel_value in pixel_values_videos
                ]
            else:
                pixel_values_videos, num_patches_videos = [], []

            pixel_values = []
            while ("<image>" in text) or ("<video>" in text):
                image_index = text.find("<image>")
                video_index = text.find("<video>")
                if image_index == -1 or (
                    video_index > -1 and video_index < image_index
                ):
                    num_patches = num_patches_videos.pop(0)
                    pixel_values.append(pixel_values_videos.pop(0))
                    context_tokens = (
                        IMG_START + IMG_CONTEXT * self.num_image_token + IMG_END
                    )
                    video_tokens = "".join(
                        [f"Frame{i + 1}: {context_tokens}" for i in range(num_patches)]
                    )
                    text = text.replace("<video>", video_tokens, 1)
                else:
                    num_patches = num_patches_images.pop(0)
                    pixel_values.append(pixel_values_images.pop(0))
                    context_tokens = IMG_CONTEXT * self.num_image_token * num_patches
                    image_tokens = IMG_START + context_tokens + IMG_END
                    text = text.replace("<image>", image_tokens, 1)
            pixel_values = torch.cat(pixel_values, dim=0)

            prompt = self.tokenizer(text, return_tensors="pt")
            prompt.update({"pixel_values": pixel_values})
            return prompt