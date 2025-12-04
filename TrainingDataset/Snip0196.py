def generate_image(cells: list[list[int]]) -> Image.Image:

    img = Image.new("RGB", (len(cells[0]), len(cells)))
    pixels = img.load()
    
    for w in range(img.width):
        for h in range(img.height):
            color = 255 - int(255 * cells[h][w])
            pixels[w, h] = (color, color, color)
    return img
