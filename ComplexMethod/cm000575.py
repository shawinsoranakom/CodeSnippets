async def _run_model_legacy(
        self,
        api_key: SecretStr,
        model_name: str,
        prompt: str,
        seed: Optional[int],
        aspect_ratio: str,
        magic_prompt_option: str,
        style_type: str,
        negative_prompt: Optional[str],
        color_palette_name: str,
        custom_colors: Optional[list[str]],
    ):
        url = "https://api.ideogram.ai/generate"
        headers = {
            "Api-Key": api_key.get_secret_value(),
            "Content-Type": "application/json",
        }

        data: Dict[str, Any] = {
            "image_request": {
                "prompt": prompt,
                "model": model_name,
                "aspect_ratio": aspect_ratio,
                "magic_prompt_option": magic_prompt_option,
            }
        }

        # Only add style_type for V2, V2_TURBO, and V3 models (V1 models don't support it)
        if model_name in ["V_2", "V_2_TURBO", "V_3"]:
            data["image_request"]["style_type"] = style_type

        if seed is not None:
            data["image_request"]["seed"] = seed

        if negative_prompt:
            data["image_request"]["negative_prompt"] = negative_prompt

        # Only add color palette for V2 and V2_TURBO models (V1 models don't support it)
        if model_name in ["V_2", "V_2_TURBO"]:
            if color_palette_name != "NONE":
                data["color_palette"] = {"name": color_palette_name}
            elif custom_colors:
                data["color_palette"] = {
                    "members": [{"color_hex": color} for color in custom_colors]
                }

        try:
            response = await Requests().post(url, headers=headers, json=data)
            return response.json()["data"][0]["url"]
        except Exception as e:
            raise ValueError(f"Failed to fetch image with legacy endpoint: {e}") from e