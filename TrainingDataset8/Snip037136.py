def create_gif(size, frames=1):
    # Create grayscale image.
    im = Image.new("L", (size, size), "white")

    images = []

    # Make circle of a constant size with a number of frames, moving across the
    # principal diagonal of a 64x64 image. The GIF will not loop and stops
    # animating after frames x 100ms.
    for i in range(0, frames):
        frame = im.copy()
        draw = ImageDraw.Draw(frame)
        pos = (i, i)
        circle_size = size / 2
        draw.ellipse([pos, tuple(p + circle_size for p in pos)], "black")
        images.append(frame.copy())

    # Save the frames as an animated GIF
    data = io.BytesIO()
    images[0].save(
        data,
        format="GIF",
        save_all=True,
        append_images=images[1:],
        duration=1,
    )

    return data.getvalue()