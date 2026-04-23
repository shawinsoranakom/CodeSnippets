def create_gif(size):
    # Create grayscale image.
    im = Image.new("L", (size, size), "white")

    images = []

    # Make ten frames with the circle of a random size and location
    random.seed(0)
    for i in range(0, 10):
        frame = im.copy()
        draw = ImageDraw.Draw(frame)
        pos = (random.randrange(0, size), random.randrange(0, size))
        circle_size = random.randrange(10, size / 2)
        draw.ellipse([pos, tuple(p + circle_size for p in pos)], "black")
        images.append(frame.copy())

    # Save the frames as an animated GIF
    data = io.BytesIO()
    images[0].save(
        data,
        format="GIF",
        save_all=True,
        append_images=images[1:],
        duration=100,
        loop=0,
    )

    return data.getvalue()