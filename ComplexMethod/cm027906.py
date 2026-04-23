async def edit_renovation_rendering(tool_context: ToolContext, inputs: EditRenovationRenderingInput) -> str:
    """
    Edits an existing renovation rendering based on feedback or refinements.

    This tool allows iterative improvements to the rendered image, such as 
    changing colors, materials, lighting, or layout elements.
    """
    if "GEMINI_API_KEY" not in os.environ and "GOOGLE_API_KEY" not in os.environ:
        raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set.")

    logger.info("Starting renovation rendering edit")

    try:
        client = genai.Client()

        # Handle inputs that might come as dict instead of Pydantic model
        if isinstance(inputs, dict):
            inputs = EditRenovationRenderingInput(**inputs)

        # Get artifact_filename from session state if not provided
        artifact_filename = inputs.artifact_filename
        if not artifact_filename:
            artifact_filename = tool_context.state.get("last_generated_rendering")
            if not artifact_filename:
                return "❌ No artifact_filename provided and no previous rendering found in session. Please generate a rendering first using generate_renovation_rendering."
            logger.info(f"Using last generated rendering from session: {artifact_filename}")

        # Validate filename format - check for common hallucination patterns
        if "_v0." in artifact_filename:
            # Version 0 doesn't exist - the first version is always v1
            logger.warning(f"Invalid version v0 detected in filename: {artifact_filename}")
            corrected_filename = artifact_filename.replace("_v0.", "_v1.")
            logger.info(f"Attempting corrected filename: {corrected_filename}")
            artifact_filename = corrected_filename

        # Load the existing rendering
        logger.info(f"Loading artifact: {artifact_filename}")
        loaded_image_part = None
        try:
            loaded_image_part = await tool_context.load_artifact(artifact_filename)
        except Exception as e:
            logger.error(f"Error loading artifact: {e}")

        # If loading failed, try to find the most recent version of this asset
        if not loaded_image_part:
            # Extract base asset name and try to find any existing version
            base_name = artifact_filename.split('_v')[0] if '_v' in artifact_filename else artifact_filename.replace('.png', '')
            asset_filenames = tool_context.state.get("asset_filenames", {})

            # Check if we have any version of this asset
            if base_name in asset_filenames:
                fallback_filename = asset_filenames[base_name]
                logger.info(f"Attempting fallback to known artifact: {fallback_filename}")
                try:
                    loaded_image_part = await tool_context.load_artifact(fallback_filename)
                    if loaded_image_part:
                        artifact_filename = fallback_filename
                        logger.info(f"Successfully loaded fallback artifact: {fallback_filename}")
                except Exception as e:
                    logger.error(f"Fallback load also failed: {e}")

            # Last resort: try the last generated rendering
            if not loaded_image_part:
                last_rendering = tool_context.state.get("last_generated_rendering")
                if last_rendering and last_rendering != artifact_filename:
                    logger.info(f"Attempting last resort fallback to: {last_rendering}")
                    try:
                        loaded_image_part = await tool_context.load_artifact(last_rendering)
                        if loaded_image_part:
                            artifact_filename = last_rendering
                            logger.info(f"Successfully loaded last resort artifact: {last_rendering}")
                    except Exception as e:
                        logger.error(f"Last resort load also failed: {e}")

        if not loaded_image_part:
            available_renderings = get_asset_versions_info(tool_context)
            return f"❌ Could not find rendering artifact: {inputs.artifact_filename}\n\n{available_renderings}\n\nPlease use one of the available artifact filenames, or generate a new rendering first."

        # Handle reference image if specified
        reference_image_part = None
        if inputs.reference_image_filename:
            if inputs.reference_image_filename == "latest":
                ref_filename = get_latest_reference_image_filename(tool_context)
            else:
                ref_filename = inputs.reference_image_filename

            if ref_filename:
                reference_image_part = await load_reference_image(tool_context, ref_filename)
                if reference_image_part:
                    logger.info(f"Using reference image for editing: {ref_filename}")

        model = "gemini-3-pro-image-preview"

        # Build content parts
        content_parts = [loaded_image_part, types.Part.from_text(text=inputs.prompt)]
        if reference_image_part:
            content_parts.append(reference_image_part)

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
                # Extract from filename
                base_name = artifact_filename.split('_v')[0] if '_v' in artifact_filename else "renovation_rendering"
                asset_name = base_name

        version = get_next_version_number(tool_context, asset_name)
        edited_artifact_filename = create_versioned_filename(asset_name, version)
        logger.info(f"Editing rendering with artifact filename: {edited_artifact_filename} (version {version})")

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
                # The inline_data already contains the mime_type from the API response
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
                    tool_context.state["last_generated_rendering"] = edited_artifact_filename
                    tool_context.state["current_asset_name"] = asset_name

                    logger.info(f"Saved edited rendering as artifact '{edited_artifact_filename}' (version {version})")

                    return f"✅ Rendering edited successfully!\n\nThe updated rendering has been saved and is available in the artifacts panel. Artifact name: {asset_name} (version {version}).\n\nNote: The image is stored as an artifact and can be accessed through the session artifacts, not as a direct image link."

                except Exception as e:
                    logger.error(f"Error saving edited artifact: {e}")
                    return f"Error saving edited rendering as artifact: {e}"
            else:
                # Log any text responses
                if hasattr(chunk, 'text') and chunk.text:
                    logger.info(f"Model response: {chunk.text}")

        return "No edited rendering was generated. Please try again."

    except Exception as e:
        logger.error(f"Error in edit_renovation_rendering: {e}")
        return f"An error occurred while editing the rendering: {e}"