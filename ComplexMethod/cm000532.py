async def generate_image(self, input_data: Input, credentials: APIKeyCredentials):
        try:
            # Handle style-based prompt modification for models without native style support
            modified_prompt = input_data.prompt
            if input_data.model not in [ImageGenModel.RECRAFT]:
                style_prefix = self._style_to_prompt_prefix(input_data.style)
                modified_prompt = f"{style_prefix} {modified_prompt}".strip()

            if input_data.model == ImageGenModel.SD3_5:
                # Use Stable Diffusion 3.5 with aspect ratio
                input_params = {
                    "prompt": modified_prompt,
                    "aspect_ratio": SIZE_TO_SD_RATIO[input_data.size],
                    "output_format": "webp",
                    "output_quality": 90,
                    "steps": 40,
                    "cfg_scale": 7.0,
                }
                output = await self._run_client(
                    credentials,
                    "stability-ai/stable-diffusion-3.5-medium",
                    input_params,
                )
                return output

            elif input_data.model == ImageGenModel.FLUX:
                # Use Flux-specific dimensions with 'jpg' format to avoid ReplicateError
                width, height = SIZE_TO_FLUX_DIMENSIONS[input_data.size]
                input_params = {
                    "prompt": modified_prompt,
                    "width": width,
                    "height": height,
                    "aspect_ratio": SIZE_TO_FLUX_RATIO[input_data.size],
                    "output_format": "jpg",  # Set to jpg for Flux models
                    "output_quality": 90,
                }
                output = await self._run_client(
                    credentials, "black-forest-labs/flux-1.1-pro", input_params
                )
                return output

            elif input_data.model == ImageGenModel.FLUX_ULTRA:
                width, height = SIZE_TO_FLUX_DIMENSIONS[input_data.size]
                input_params = {
                    "prompt": modified_prompt,
                    "width": width,
                    "height": height,
                    "aspect_ratio": SIZE_TO_FLUX_RATIO[input_data.size],
                    "output_format": "jpg",
                    "output_quality": 90,
                }
                output = await self._run_client(
                    credentials, "black-forest-labs/flux-1.1-pro-ultra", input_params
                )
                return output

            elif input_data.model == ImageGenModel.RECRAFT:
                input_params = {
                    "prompt": input_data.prompt,
                    "size": SIZE_TO_RECRAFT_DIMENSIONS[input_data.size],
                    "style": input_data.style.value,
                }
                output = await self._run_client(
                    credentials, "recraft-ai/recraft-v3", input_params
                )
                return output

            elif input_data.model in (
                ImageGenModel.NANO_BANANA_PRO,
                ImageGenModel.NANO_BANANA_2,
            ):
                # Use Nano Banana models (Google Gemini image variants)
                model_map = {
                    ImageGenModel.NANO_BANANA_PRO: "google/nano-banana-pro",
                    ImageGenModel.NANO_BANANA_2: "google/nano-banana-2",
                }
                input_params = {
                    "prompt": modified_prompt,
                    "aspect_ratio": SIZE_TO_NANO_BANANA_RATIO[input_data.size],
                    "resolution": "2K",
                    "output_format": "jpg",
                    "safety_filter_level": "block_only_high",
                }
                output = await self._run_client(
                    credentials, model_map[input_data.model], input_params
                )
                return output

        except Exception as e:
            raise RuntimeError(f"Failed to generate image: {str(e)}")