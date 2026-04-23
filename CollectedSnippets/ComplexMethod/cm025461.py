def turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        color: tuple[int, int, int] | None = kwargs.get(ATTR_RGB_COLOR)
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        transition: float | None = kwargs.get(ATTR_TRANSITION)

        command_id = "exact"
        command_args: dict[str, str] = {}

        # set color levels
        if color is not None:
            if not any(color):
                color = (255, 255, 255)
            command_args.update(
                {"red": str(color[0]), "green": str(color[1]), "blue": str(color[2])}
            )
        elif brightness is not None:
            command_args["level"] = str(round(brightness / 2.55))
        elif transition is not None:
            command_args["level"] = "100"
        else:
            command_id = "on"

        if transition is not None:
            command_id = "exactSmooth"
            if transition < 127:
                duration = round(transition)
            else:
                duration = min(127, round((transition) / 60)) + 127
            command_args["duration"] = str(duration)

        cmd = command_id
        if command_args:
            cmd = f"{command_id}?{'&'.join(f'{argId}={argVal}' for argId, argVal in command_args.items())}"
        self.controller.zwave_api.send_command(self.device.id, cmd)