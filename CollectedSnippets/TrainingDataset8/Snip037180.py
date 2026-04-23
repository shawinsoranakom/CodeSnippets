def create_image(self):
        # Create a new image
        self._image = Image.new("RGB", (self._size, self._size))
        d = ImageDraw.Draw(self._image)

        # Draw a red square
        d.rectangle(
            [
                (self._step, self._step),
                (self._half - self._step, self._half - self._step),
            ],
            fill="red",
            outline=None,
            width=0,
        )

        # Draw a green circle.  In PIL, green is 00800, lime is 00ff00
        d.ellipse(
            [
                (self._half + self._step, self._step),
                (self._size - self._step, self._half - self._step),
            ],
            fill="lime",
            outline=None,
            width=0,
        )

        # Draw a blue triangle
        d.polygon(
            [
                (self._half / 2, self._half + self._step),
                (self._half - self._step, self._size - self._step),
                (self._step, self._size - self._step),
            ],
            fill="blue",
            outline=None,
        )

        # Creating a pie slice shaped 'mask' ie an alpha channel.
        alpha = Image.new("L", self._image.size, "white")
        d = ImageDraw.Draw(alpha)
        d.pieslice(
            [
                (self._step * 3, self._step * 3),
                (self._size - self._step, self._size - self._step),
            ],
            0,
            90,
            fill="black",
            outline=None,
            width=0,
        )
        self._image.putalpha(alpha)