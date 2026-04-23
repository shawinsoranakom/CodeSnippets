async def run(
        self,
        input_data: Input,
        *,
        credentials: APIKeyCredentials,
        execution_context: ExecutionContext,
        **kwargs,
    ) -> BlockOutput:
        # Build the modifications array
        modifications = []

        # Add text modifications
        for text_mod in input_data.text_modifications:
            mod_data: Dict[str, Any] = {
                "name": text_mod.name,
                "text": text_mod.text,
            }

            # Add optional text styling parameters only if they have values
            if text_mod.color and text_mod.color.strip():
                mod_data["color"] = text_mod.color
            if text_mod.font_family and text_mod.font_family.strip():
                mod_data["font_family"] = text_mod.font_family
            if text_mod.font_size and text_mod.font_size > 0:
                mod_data["font_size"] = text_mod.font_size
            if text_mod.font_weight and text_mod.font_weight.strip():
                mod_data["font_weight"] = text_mod.font_weight
            if text_mod.text_align and text_mod.text_align.strip():
                mod_data["text_align"] = text_mod.text_align

            modifications.append(mod_data)

        # Add image modification if provided and not empty
        if input_data.image_url and input_data.image_url.strip():
            modifications.append(
                {
                    "name": input_data.image_layer_name,
                    "image_url": input_data.image_url,
                }
            )

        # Build the request payload - only include non-empty optional fields
        payload = {
            "template": input_data.template_id,
            "modifications": modifications,
        }

        # Add project_id if provided (required for Master API keys)
        if input_data.project_id and input_data.project_id.strip():
            payload["project_id"] = input_data.project_id

        if input_data.webhook_url and input_data.webhook_url.strip():
            payload["webhook_url"] = input_data.webhook_url
        if input_data.metadata and input_data.metadata.strip():
            payload["metadata"] = input_data.metadata

        # Make the API request using the private method
        data = await self._make_api_request(
            payload, credentials.api_key.get_secret_value()
        )

        # Synchronous request - image should be ready
        yield "success", True

        # Store the generated image to workspace for persistence
        image_url = data.get("image_url", "")
        if image_url:
            stored_url = await store_media_file(
                file=MediaFileType(image_url),
                execution_context=execution_context,
                return_format="for_block_output",
            )
            yield "image_url", stored_url
        else:
            yield "image_url", ""

        yield "uid", data.get("uid", "")
        yield "status", data.get("status", "completed")