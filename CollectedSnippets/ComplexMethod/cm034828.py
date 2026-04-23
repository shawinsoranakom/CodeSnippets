async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute image generation

        Returns:
            Dict[str, Any]: Generated image data or error message
        """
        from ..client import AsyncClient

        prompt = arguments.get("prompt", "")
        model = arguments.get("model", "flux")
        width = arguments.get("width", 1024)
        height = arguments.get("height", 1024)

        if not prompt:
            return {
                "error": "Prompt parameter is required"
            }

        try:
            # Generate image using gpt4free client
            client = AsyncClient()

            response = await client.images.generate(
                model=model,
                prompt=prompt,
                width=width,
                height=height
            )

            # Get the image data with proper validation
            if not response:
                return {
                    "error": "Image generation failed: No response from provider"
                }

            if not hasattr(response, 'data') or not response.data:
                return {
                    "error": "Image generation failed: No image data in response"
                }

            if len(response.data) == 0:
                return {
                    "error": "Image generation failed: Empty image data array"
                }

            image_data = response.data[0]

            # Check if image_data has url attribute
            if not hasattr(image_data, 'url'):
                return {
                    "error": "Image generation failed: No URL in image data"
                }

            image_url = image_data.url

            template = 'Display the image using this template: <a href="{image}" data-width="{width}" data-height="{height}"><img src="{image}" alt="{prompt}"></a>'

            # Return result based on URL type
            if image_url.startswith('data:'):
                return {
                    "prompt": prompt,
                    "model": model,
                    "width": width,
                    "height": height,
                    "image": image_url,
                    "template": template
                }
            else:
                if arguments.get("origin") and image_url.startswith("/media/"):
                    image_url = f"{arguments.get('origin')}{image_url}"
                return {
                    "prompt": prompt,
                    "model": model,
                    "width": width,
                    "height": height,
                    "image_url": image_url,
                    "template": template
                }

        except Exception as e:
            return {
                "error": f"Image generation failed: {str(e)}"
            }