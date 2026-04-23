async def generate_agent_image_v1(agent: GraphBaseMeta | AgentGraph) -> io.BytesIO:
    """
    Generate an image for an agent using Flux model via Replicate API.

    Args:
        agent (GraphBaseMeta | AgentGraph): The agent to generate an image for

    Returns:
        io.BytesIO: The generated image as bytes
    """
    try:
        if not settings.secrets.replicate_api_key:
            raise ValueError("Missing Replicate API key in settings")

        # Construct prompt from agent details
        prompt = (
            "Create a visually engaging app store thumbnail for the AI agent "
            "that highlights what it does in a clear and captivating way:\n"
            f"- **Name**: {agent.name}\n"
            f"- **Description**: {agent.description}\n"
            f"Focus on showcasing its core functionality with an appealing design."
        )

        # Set up Replicate client
        client = ReplicateClient(api_token=settings.secrets.replicate_api_key)

        # Model parameters
        input_data = {
            "prompt": prompt,
            "width": 1024,
            "height": 768,
            "aspect_ratio": "4:3",
            "output_format": "jpg",
            "output_quality": 90,
            "num_inference_steps": 30,
            "guidance": 3.5,
            "negative_prompt": "blurry, low quality, distorted, deformed",
            "disable_safety_checker": True,
        }

        try:
            # Run model
            output = client.run("black-forest-labs/flux-1.1-pro", input=input_data)

            # Depending on the model output, extract the image URL or bytes
            # If the output is a list of FileOutput or URLs
            if isinstance(output, list) and output:
                if isinstance(output[0], FileOutput):
                    image_bytes = output[0].read()
                else:
                    # If it's a URL string, fetch the image bytes
                    result_url = output[0]
                    response = await Requests().get(result_url)
                    image_bytes = response.content
            elif isinstance(output, FileOutput):
                image_bytes = output.read()
            elif isinstance(output, str):
                # Output is a URL
                response = await Requests().get(output)
                image_bytes = response.content
            else:
                raise RuntimeError("Unexpected output format from the model.")

            return io.BytesIO(image_bytes)

        except ReplicateError as e:
            if e.status == 401:
                raise RuntimeError("Invalid Replicate API token") from e
            raise RuntimeError(f"Replicate API error: {str(e)}") from e

    except Exception as e:
        logger.exception("Failed to generate agent image")
        raise RuntimeError(f"Image generation failed: {str(e)}")