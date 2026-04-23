async def execute(
        cls,
        prompt,
        turbo=False,
        aspect_ratio="1:1",
        magic_prompt_option="AUTO",
        seed=0,
        negative_prompt="",
        num_images=1,
    ):
        # Determine the model based on turbo setting
        aspect_ratio = V1_V2_RATIO_MAP.get(aspect_ratio, None)
        model = "V_1_TURBO" if turbo else "V_1"

        response = await sync_op(
            cls,
            ApiEndpoint(path="/proxy/ideogram/generate", method="POST"),
            response_model=IdeogramGenerateResponse,
            data=IdeogramGenerateRequest(
                image_request=ImageRequest(
                    prompt=prompt,
                    model=model,
                    num_images=num_images,
                    seed=seed,
                    aspect_ratio=aspect_ratio if aspect_ratio != "ASPECT_1_1" else None,
                    magic_prompt_option=(magic_prompt_option if magic_prompt_option != "AUTO" else None),
                    negative_prompt=negative_prompt if negative_prompt else None,
                )
            ),
            max_retries=1,
        )

        if not response.data or len(response.data) == 0:
            raise Exception("No images were generated in the response")

        image_urls = [image_data.url for image_data in response.data if image_data.url]
        if not image_urls:
            raise Exception("No image URLs were generated in the response")
        return IO.NodeOutput(await download_and_process_images(image_urls))