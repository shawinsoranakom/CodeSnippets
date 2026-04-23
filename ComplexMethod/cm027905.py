async def generate_renovation_rendering(tool_context: ToolContext, inputs: GenerateRenovationRenderingInput) -> str:
    """
    Generates a photorealistic rendering of a renovated space based on the design plan.

    This tool uses Gemini 3 Pro's image generation capabilities to create visual 
    representations of renovation plans. It can optionally use current room photos 
    and inspiration images as references.
    """
    if "GEMINI_API_KEY" not in os.environ and "GOOGLE_API_KEY" not in os.environ:
        raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set.")

    logger.info("Starting renovation rendering generation")
    try:
        client = genai.Client()

        # Handle inputs that might come as dict instead of Pydantic model
        if isinstance(inputs, dict):
            inputs = GenerateRenovationRenderingInput(**inputs)

        # Handle reference images (current room photo or inspiration)
        reference_images = []

        if inputs.current_room_photo:
            current_photo_part = await load_reference_image(tool_context, inputs.current_room_photo)
            if current_photo_part:
                reference_images.append(current_photo_part)
                logger.info(f"Using current room photo: {inputs.current_room_photo}")

        if inputs.inspiration_image:
            if inputs.inspiration_image == "latest":
                insp_filename = get_latest_reference_image_filename(tool_context)
            else:
                insp_filename = inputs.inspiration_image

            if insp_filename:
                inspiration_part = await load_reference_image(tool_context, insp_filename)
                if inspiration_part:
                    reference_images.append(inspiration_part)
                    logger.info(f"Using inspiration image: {insp_filename}")

        # Build the enhanced prompt using SLC formula (Subject, Lighting, Camera)
        base_rewrite_prompt = f"""
        Create an ultra-detailed, photorealistic prompt for generating a professional interior design photograph.

        Original description: {inputs.prompt}

        **CRITICAL REQUIREMENT - PRESERVE EXACT LAYOUT:**
        The generated image MUST maintain the EXACT same room layout, structure, and spatial arrangement described in the prompt:
        - Keep all windows, doors, skylights in their exact positions
        - Keep all cabinets, counters, appliances in their exact positions
        - Keep the same room dimensions and proportions
        - Keep the same camera angle/perspective
        - ONLY change surface finishes: paint colors, cabinet colors, countertop materials, flooring, backsplash, hardware, and decorative elements
        - DO NOT move, add, or remove any structural elements or major fixtures

        **Use the SLC Formula for Photorealism:**

        1. **SUBJECT (S)** - Be highly specific about details and textures:
           - Describe exact materials with rich adjectives (e.g., "smooth matte white shaker-style cabinets", "honed Carrara marble countertops with subtle grey veining")
           - Include texture details (e.g., "brushed nickel hardware", "wide-plank oak flooring with natural grain")
           - Specify finishes precisely (e.g., "satin finish", "polished", "matte", "textured")

        2. **LIGHTING (L)** - Describe lighting conditions that create mood and realism:
           - Natural light sources (e.g., "soft morning sunlight streaming through windows", "golden hour warm glow")
           - Artificial lighting (e.g., "warm LED under-cabinet lighting", "pendant lights casting gentle shadows")
           - Light quality (e.g., "diffused natural light", "dramatic side lighting", "even ambient illumination")
           - Shadows and highlights (e.g., "subtle shadows adding depth", "highlights on polished surfaces")

        3. **CAMERA (C)** - Include professional photography specifications:
           - Camera type: "shot on professional DSLR" or "architectural photography camera"
           - Resolution: "8K resolution", "ultra high definition", "HDR"
           - Perspective: specific angle (e.g., "wide-angle lens from doorway", "eye-level perspective", "slightly elevated view")
           - Depth of field: "sharp focus throughout" or "shallow depth of field with background blur"
           - Quality keywords: "professional interior design photography", "magazine quality", "architectural digest style"

        **Additional Requirements:**
        - Maintain existing spatial layout and dimensions exactly as described
        - Include specific color names and codes when mentioned
        - Add atmospheric details (e.g., "clean, inviting atmosphere", "modern luxury feel")
        - Specify the aspect ratio: {inputs.aspect_ratio}

        **Output Format:** Create a single, flowing paragraph that reads like a professional photography brief. 
        Start with the camera/technical specs, then describe the subject with rich detail, then lighting conditions.
        Include keywords: "photorealistic", "8K", "HDR", "professional interior photography", "architectural photography".
        Emphasize that the layout must remain unchanged - only surface finishes are modified.
        """

        if reference_images:
            base_rewrite_prompt += "\n\n**Reference Image Layout:** The reference image shows the EXACT layout that must be preserved. Match the camera angle, room structure, window/door positions, and furniture/appliance placement EXACTLY. Only change the surface finishes and colors. Analyze the lighting in the reference image and replicate it."

        # Get enhanced prompt
        rewritten_prompt_response = client.models.generate_content(
            model="gemini-3-pro-preview", 
            contents=base_rewrite_prompt
        )
        rewritten_prompt = rewritten_prompt_response.text
        logger.info(f"Enhanced prompt: {rewritten_prompt}")

        model = "gemini-3-pro-image-preview"

        # Build content parts
        content_parts = [types.Part.from_text(text=rewritten_prompt)]
        content_parts.extend(reference_images)

        contents = [
            types.Content(
                role="user",
                parts=content_parts,
            ),
        ]

        generate_content_config = types.GenerateContentConfig(
            response_modalities=[
                "IMAGE",
                "TEXT",
            ],
        )

        # Generate versioned filename
        version = get_next_version_number(tool_context, inputs.asset_name)
        artifact_filename = create_versioned_filename(inputs.asset_name, version)
        logger.info(f"Generating rendering with artifact filename: {artifact_filename} (version {version})")

        # Generate the image
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if (
                chunk.candidates is None
                or chunk.candidates[0].content is None
                or chunk.candidates[0].content.parts is None
            ):
                continue

            if chunk.candidates[0].content.parts[0].inline_data and chunk.candidates[0].content.parts[0].inline_data.data:
                inline_data = chunk.candidates[0].content.parts[0].inline_data

                # Create a Part object from the inline data
                # The inline_data already contains the mime_type from the API response
                image_part = types.Part(inline_data=inline_data)

                try:
                    # Save the image as an artifact
                    version = await tool_context.save_artifact(
                        filename=artifact_filename, 
                        artifact=image_part
                    )

                    # Update version tracking
                    update_asset_version(tool_context, inputs.asset_name, version, artifact_filename)

                    # Store in session state
                    tool_context.state["last_generated_rendering"] = artifact_filename
                    tool_context.state["current_asset_name"] = inputs.asset_name

                    logger.info(f"Saved rendering as artifact '{artifact_filename}' (version {version})")

                    return f"✅ Renovation rendering generated successfully!\n\nThe rendering has been saved and is available in the artifacts panel. Artifact name: {inputs.asset_name} (version {version}).\n\nNote: The image is stored as an artifact and can be accessed through the session artifacts, not as a direct image link."

                except Exception as e:
                    logger.error(f"Error saving artifact: {e}")
                    return f"Error saving rendering as artifact: {e}"
            else:
                # Log any text responses
                if hasattr(chunk, 'text') and chunk.text:
                    logger.info(f"Model response: {chunk.text}")

        return "No rendering was generated. Please try again with a more detailed prompt."

    except Exception as e:
        logger.error(f"Error in generate_renovation_rendering: {e}")
        return f"An error occurred while generating the rendering: {e}"