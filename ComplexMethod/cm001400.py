def generate_image(self, prompt: str, size: int) -> str:
        """Generate an image from a prompt.

        Args:
            prompt (str): The prompt to use
            size (int, optional): The size of the image. Defaults to 256.
                Not supported by HuggingFace.

        Returns:
            str: The filename of the image
        """
        filename = self.workspace.root / f"{str(uuid.uuid4())}.jpg"

        if self.openai_credentials and (
            self.config.image_provider == "dalle"
            or not (self.config.huggingface_api_token or self.config.sd_webui_url)
        ):
            return self.generate_image_with_dalle(prompt, filename, size)

        elif self.config.huggingface_api_token and (
            self.config.image_provider == "huggingface"
            or not (self.openai_credentials or self.config.sd_webui_url)
        ):
            return self.generate_image_with_hf(prompt, filename)

        elif self.config.sd_webui_url and (
            self.config.image_provider == "sdwebui" or self.config.sd_webui_auth
        ):
            return self.generate_image_with_sd_webui(prompt, filename, size)

        return "Error: No image generation provider available"