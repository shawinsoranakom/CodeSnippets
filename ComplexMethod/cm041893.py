def display_output(output):
    if in_jupyter_notebook():
        from IPython.display import HTML, Image, Javascript, display

        if output["type"] == "console":
            print(output["content"])
        elif output["type"] == "image":
            if "base64" in output["format"]:
                # Decode the base64 image data
                image_data = base64.b64decode(output["content"])
                display(Image(image_data))
            elif output["format"] == "path":
                # Display the image file on the system
                display(Image(filename=output["content"]))
        elif "format" in output and output["format"] == "html":
            display(HTML(output["content"]))
        elif "format" in output and output["format"] == "javascript":
            display(Javascript(output["content"]))
    else:
        display_output_cli(output)

    # Return a message for the LLM.
    # We should make this specific to what happened in the future,
    # like saying WHAT temporary file we made, etc. Keep the LLM informed.
    return "Displayed on the user's machine."