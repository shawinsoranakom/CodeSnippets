def generate_images(cells: list[list[int]], frames: int) -> list[Image.Image]:
    
    images = []
    for _ in range(frames):

      img = Image.new("RGB", (len(cells[0]), len(cells)))
        pixels = img.load()

        for x in range(len(cells)):
            for y in range(len(cells[0])):
                colour = 255 - cells[y][x] * 255
                pixels[x, y] = (colour, colour, colour)

        images.append(img)
        cells = new_generation(cells)
    return images
