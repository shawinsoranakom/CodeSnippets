def _insert_media_placeholders(
        self,
        text: list[str],
        image_pixel_values,
        video_pixel_values,
        image_num_patches: list[int],
        video_num_patches: list[int],
        image_num_patches_indices: np.ndarray,
        video_num_patches_indices: np.ndarray,
        video_patch_indices: np.ndarray,
    ):
        """
        Processes interleaved text with <image> and <video> placeholders, replacing them with appropriate
        image and video tokens while keeping track of the patches used.
        """
        image_index = 0
        video_index = 0
        processed_text = []
        image_video_patches = []
        replace_strings = []
        # Support interleaved image and video in prompts:
        # Processed patches of images and videos are inserted in `image_video_patches` in the order they appear in the prompts
        for prompt in text:
            new_prompt = prompt
            while self.image_token in new_prompt or self.video_token in new_prompt:
                if self.image_token in new_prompt and (
                    self.video_token not in new_prompt
                    or new_prompt.index(self.image_token) < new_prompt.index(self.video_token)
                ):
                    # Get the slice of patches corresponding to the current image
                    start_index = image_num_patches_indices[image_index - 1] if image_index > 0 else 0
                    end_index = image_num_patches_indices[image_index]
                    image_video_patches.append(image_pixel_values[start_index:end_index])
                    # Replace the corresponding image placeholder with the correct number of image tokens
                    new_prompt = new_prompt.replace(self.image_token, "<placeholder>", 1)
                    replace_strings.append(
                        f"{self.start_image_token}{self.image_token * self.image_seq_length * image_num_patches[image_index]}{self.end_image_token}"
                    )
                    image_index += 1
                else:
                    # Get the slice of patches corresponding to the current video
                    # Here we need to account for both the multiple video frames and the potential multiple patches per frame
                    # As of now, InternVL only supports one patch per frame, but we keep the code flexible for future updates
                    current_patch_index = video_patch_indices[video_index]
                    end_patch_index = video_patch_indices[video_index + 1]
                    start_index = video_num_patches_indices[current_patch_index]
                    end_index = video_num_patches_indices[end_patch_index]
                    image_video_patches.append(video_pixel_values[start_index:end_index])
                    # Get the number of patches per frame and replace the video placeholder with the correct number of image tokens
                    num_patches = list(video_num_patches[current_patch_index:end_patch_index])
                    video_prompt = "\n".join(
                        f"Frame{i + 1}: {self.start_image_token}{self.image_token * self.image_seq_length * num_patches[i]}{self.end_image_token}"
                        for i in range(len(num_patches))
                    )
                    replace_strings.append(video_prompt)
                    new_prompt = new_prompt.replace(self.video_token, "<placeholder>", 1)
                    video_index += 1
            while "<placeholder>" in new_prompt:
                replace_str = replace_strings.pop(0)
                new_prompt = new_prompt.replace("<placeholder>", replace_str, 1)
            processed_text.append(new_prompt)

        return processed_text, image_video_patches, image_index, video_index