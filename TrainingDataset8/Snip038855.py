def create_image(size, format="RGB", add_alpha=True):
    step = 1
    half = size / 2
    # Create a new image
    image = Image.new("RGB", (size, size))
    d = ImageDraw.Draw(image)
    # Draw a red square
    d.rectangle(
        [(step, step), (half - step, half - step)], fill="red", outline=None, width=0
    )
    # Draw a green circle.  In PIL, green is 00800, lime is 00ff00
    d.ellipse(
        [(half + step, step), (size - step, half - step)],
        fill="lime",
        outline=None,
        width=0,
    )
    # Draw a blue triangle
    d.polygon(
        [(half / 2, half + step), (half - step, size - step), (step, size - step)],
        fill="blue",
        outline=None,
    )
    if add_alpha:
        # Creating a pie slice shaped 'mask' ie an alpha channel.
        alpha = Image.new("L", image.size, "white")
        d = ImageDraw.Draw(alpha)
        d.pieslice(
            [(step * 3, step * 3), (size - step, size - step)],
            0,
            90,
            fill="black",
            outline=None,
            width=0,
        )
        image.putalpha(alpha)

    if format == "BGR":
        return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    else:
        return image