async def execute(
        cls,
        prompt,
        image=None,
        mask=None,
        resolution="Auto",
        aspect_ratio="1:1",
        magic_prompt_option="AUTO",
        seed=0,
        num_images=1,
        rendering_speed="DEFAULT",
        character_image=None,
        character_mask=None,
    ):
        if rendering_speed == "BALANCED":  # for backward compatibility
            rendering_speed = "DEFAULT"

        character_img_binary = None
        character_mask_binary = None

        if character_image is not None:
            input_tensor = character_image.squeeze().cpu()
            if character_mask is not None:
                character_mask = resize_mask_to_image(character_mask, character_image, allow_gradient=False)
                character_mask = 1.0 - character_mask
                if character_mask.shape[1:] != character_image.shape[1:-1]:
                    raise Exception("Character mask and image must be the same size")

                mask_np = (character_mask.squeeze().cpu().numpy() * 255).astype(np.uint8)
                mask_img = Image.fromarray(mask_np)
                mask_byte_arr = BytesIO()
                mask_img.save(mask_byte_arr, format="PNG")
                mask_byte_arr.seek(0)
                character_mask_binary = mask_byte_arr
                character_mask_binary.name = "mask.png"

            img_np = (input_tensor.numpy() * 255).astype(np.uint8)
            img = Image.fromarray(img_np)
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format="PNG")
            img_byte_arr.seek(0)
            character_img_binary = img_byte_arr
            character_img_binary.name = "image.png"
        elif character_mask is not None:
            raise Exception("Character mask requires character image to be present")

        # Check if both image and mask are provided for editing mode
        if image is not None and mask is not None:
            # Process image and mask
            input_tensor = image.squeeze().cpu()
            # Resize mask to match image dimension
            mask = resize_mask_to_image(mask, image, allow_gradient=False)
            # Invert mask, as Ideogram API will edit black areas instead of white areas (opposite of convention).
            mask = 1.0 - mask

            # Validate mask dimensions match image
            if mask.shape[1:] != image.shape[1:-1]:
                raise Exception("Mask and Image must be the same size")

            # Process image
            img_np = (input_tensor.numpy() * 255).astype(np.uint8)
            img = Image.fromarray(img_np)
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format="PNG")
            img_byte_arr.seek(0)
            img_binary = img_byte_arr
            img_binary.name = "image.png"

            # Process mask - white areas will be replaced
            mask_np = (mask.squeeze().cpu().numpy() * 255).astype(np.uint8)
            mask_img = Image.fromarray(mask_np)
            mask_byte_arr = BytesIO()
            mask_img.save(mask_byte_arr, format="PNG")
            mask_byte_arr.seek(0)
            mask_binary = mask_byte_arr
            mask_binary.name = "mask.png"

            # Create edit request
            edit_request = IdeogramV3EditRequest(
                prompt=prompt,
                rendering_speed=rendering_speed,
            )

            # Add optional parameters
            if magic_prompt_option != "AUTO":
                edit_request.magic_prompt = magic_prompt_option
            if seed != 0:
                edit_request.seed = seed
            if num_images > 1:
                edit_request.num_images = num_images

            files = {
                "image": img_binary,
                "mask": mask_binary,
            }
            if character_img_binary:
                files["character_reference_images"] = character_img_binary
            if character_mask_binary:
                files["character_mask_binary"] = character_mask_binary

            response = await sync_op(
                cls,
                ApiEndpoint(path="/proxy/ideogram/ideogram-v3/edit", method="POST"),
                response_model=IdeogramGenerateResponse,
                data=edit_request,
                files=files,
                content_type="multipart/form-data",
                max_retries=1,
            )

        elif image is not None or mask is not None:
            # If only one of image or mask is provided, raise an error
            raise Exception("Ideogram V3 image editing requires both an image AND a mask")
        else:
            # Create generation request
            gen_request = IdeogramV3Request(
                prompt=prompt,
                rendering_speed=rendering_speed,
            )

            # Handle resolution vs aspect ratio
            if resolution != "Auto":
                gen_request.resolution = resolution
            elif aspect_ratio != "1:1":
                v3_aspect = V3_RATIO_MAP.get(aspect_ratio)
                if v3_aspect:
                    gen_request.aspect_ratio = v3_aspect

            # Add optional parameters
            if magic_prompt_option != "AUTO":
                gen_request.magic_prompt = magic_prompt_option
            if seed != 0:
                gen_request.seed = seed
            if num_images > 1:
                gen_request.num_images = num_images

            files = {}
            if character_img_binary:
                files["character_reference_images"] = character_img_binary
            if character_mask_binary:
                files["character_mask_binary"] = character_mask_binary
            if files:
                gen_request.style_type = "AUTO"

            response = await sync_op(
                cls,
                endpoint=ApiEndpoint(path="/proxy/ideogram/ideogram-v3/generate", method="POST"),
                response_model=IdeogramGenerateResponse,
                data=gen_request,
                files=files if files else None,
                content_type="multipart/form-data",
                max_retries=1,
            )

        if not response.data or len(response.data) == 0:
            raise Exception("No images were generated in the response")

        image_urls = [image_data.url for image_data in response.data if image_data.url]
        if not image_urls:
            raise Exception("No image URLs were generated in the response")
        return IO.NodeOutput(await download_and_process_images(image_urls))