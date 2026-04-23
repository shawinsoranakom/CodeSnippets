async def generate_improved_landing_page(tool_context: ToolContext, inputs: GenerateImprovedLandingPageInput) -> str:
    """
    Generates an improved landing page based on the analysis and feedback.

    This tool creates a new landing page design incorporating all the recommended
    UI/UX improvements. Can work with or without a reference image.
    """
    if "GEMINI_API_KEY" not in os.environ and "GOOGLE_API_KEY" not in os.environ:
        raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set.")

    logger.info("Starting improved landing page generation")

    try:
        client = genai.Client()
        inputs = GenerateImprovedLandingPageInput(**inputs)

        # Note: Reference images from the conversation are automatically available to agents
        # This parameter is kept for backwards compatibility with saved artifacts
        reference_part = None
        if inputs.reference_image:
            try:
                reference_part = await load_landing_page_image(tool_context, inputs.reference_image)
                if reference_part:
                    logger.info(f"Using reference image artifact: {inputs.reference_image}")
            except Exception as e:
                logger.warning(f"Could not load reference image, proceeding without it: {e}")

        # Get the analysis from state to incorporate feedback
        latest_analysis = tool_context.state.get("latest_analysis", "")

        # Build enhanced prompt
        enhancement_prompt = f"""
Create a professional landing page design that incorporates these improvements:

{inputs.prompt}

**Previous Analysis Insights:**
{latest_analysis[:500] if latest_analysis else "No previous analysis available"}

**Design Requirements:**
- Modern, clean aesthetic
- Clear visual hierarchy
- Prominent, well-designed CTAs
- Proper whitespace and breathing room
- Professional typography with clear hierarchy
- Accessible color contrast (WCAG AA)
- Mobile-first responsive considerations
- Follow the latest UI/UX best practices
- High-quality, photorealistic rendering

Aspect ratio: {inputs.aspect_ratio}

Create a professional UI/UX design that would be magazine-quality.
"""

        # Prepare content parts
        content_parts = [types.Part.from_text(text=enhancement_prompt)]
        if reference_part:
            content_parts.append(reference_part)

        # Generate enhanced prompt first
        rewritten_prompt_response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=enhancement_prompt
        )
        rewritten_prompt = rewritten_prompt_response.text
        logger.info(f"Enhanced prompt: {rewritten_prompt}")

        model = "gemini-2.5-flash-image"

        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=rewritten_prompt)] + ([reference_part] if reference_part else []),
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
        logger.info(f"Generating improved landing page with filename: {artifact_filename} (version {version})")

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

                image_part = types.Part(inline_data=inline_data)

                try:
                    version = await tool_context.save_artifact(
                        filename=artifact_filename, 
                        artifact=image_part
                    )

                    update_asset_version(tool_context, inputs.asset_name, version, artifact_filename)

                    tool_context.state["last_generated_landing_page"] = artifact_filename
                    tool_context.state["current_asset_name"] = inputs.asset_name

                    logger.info(f"Saved improved landing page as artifact '{artifact_filename}' (version {version})")

                    return f"✅ **Improved landing page generated successfully!**\n\nSaved as: **{artifact_filename}** (version {version} of {inputs.asset_name})\n\nThis design incorporates all the recommended UI/UX improvements."

                except Exception as e:
                    logger.error(f"Error saving artifact: {e}")
                    return f"Error saving improved landing page as artifact: {e}"
            else:
                if hasattr(chunk, 'text') and chunk.text:
                    logger.info(f"Model response: {chunk.text}")

        return "No improved landing page was generated. Please try again with a more detailed prompt."

    except Exception as e:
        logger.error(f"Error in generate_improved_landing_page: {e}")
        return f"An error occurred while generating the improved landing page: {e}"