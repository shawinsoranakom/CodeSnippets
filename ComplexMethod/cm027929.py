async def edit_landing_page_image(tool_context: ToolContext, inputs: EditLandingPageInput) -> str:
    """
    Edits a landing page image by applying UI/UX improvements.

    This tool uses Gemini 2.5 Flash's image generation capabilities to create
    an improved version of the landing page based on feedback.
    """
    if "GEMINI_API_KEY" not in os.environ and "GOOGLE_API_KEY" not in os.environ:
        raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set.")

    logger.info("Starting landing page image editing")

    try:
        client = genai.Client()
        inputs = EditLandingPageInput(**inputs)

        # Load the existing landing page image
        logger.info(f"Loading artifact: {inputs.artifact_filename}")
        try:
            loaded_image_part = await tool_context.load_artifact(inputs.artifact_filename)
            if not loaded_image_part:
                return f"❌ Could not find landing page artifact: {inputs.artifact_filename}"
        except Exception as e:
            logger.error(f"Error loading artifact: {e}")
            return f"Error loading landing page artifact: {e}"

        model = "gemini-2.5-flash-image"

        # Build edit prompt with UI/UX best practices
        enhanced_prompt = f"""
{inputs.prompt}

**Apply these UI/UX best practices while editing:**
- Maintain visual hierarchy (size, color, spacing)
- Ensure sufficient whitespace for breathing room
- Use consistent alignment and grid system
- Make CTAs prominent with contrasting colors
- Improve readability (font size, line height, contrast)
- Follow modern web design principles
- Keep the overall brand aesthetic

Make the improvements look natural and professional.
"""

        # Build content parts
        content_parts = [loaded_image_part, types.Part.from_text(text=enhanced_prompt)]

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

        # Determine asset name and generate versioned filename
        if inputs.asset_name:
            asset_name = inputs.asset_name
        else:
            current_asset_name = tool_context.state.get("current_asset_name")
            if current_asset_name:
                asset_name = current_asset_name
            else:
                base_name = inputs.artifact_filename.split('_v')[0] if '_v' in inputs.artifact_filename else "landing_page"
                asset_name = base_name

        version = get_next_version_number(tool_context, asset_name)
        edited_artifact_filename = create_versioned_filename(asset_name, version)
        logger.info(f"Editing landing page with artifact filename: {edited_artifact_filename} (version {version})")

        # Edit the image
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
                edited_image_part = types.Part(inline_data=inline_data)

                try:
                    # Save the edited image as an artifact
                    version = await tool_context.save_artifact(
                        filename=edited_artifact_filename, 
                        artifact=edited_image_part
                    )

                    # Update version tracking
                    update_asset_version(tool_context, asset_name, version, edited_artifact_filename)

                    # Store in session state
                    tool_context.state["last_edited_landing_page"] = edited_artifact_filename
                    tool_context.state["current_asset_name"] = asset_name

                    logger.info(f"Saved edited landing page as artifact '{edited_artifact_filename}' (version {version})")

                    return f"✅ **Landing page edited successfully!**\n\nSaved as: **{edited_artifact_filename}** (version {version} of {asset_name})\n\nThe landing page has been improved with the UI/UX enhancements."

                except Exception as e:
                    logger.error(f"Error saving edited artifact: {e}")
                    return f"Error saving edited landing page as artifact: {e}"
            else:
                if hasattr(chunk, 'text') and chunk.text:
                    logger.info(f"Model response: {chunk.text}")

        return "No edited landing page was generated. Please try again."

    except Exception as e:
        logger.error(f"Error in edit_landing_page_image: {e}")
        return f"An error occurred while editing the landing page: {e}"