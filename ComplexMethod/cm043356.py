def _log(
        self,
        level: LogLevel,
        message: str,
        tag: str,
        params: Optional[Dict[str, Any]] = None,
        colors: Optional[Dict[str, LogColor]] = None,
        boxes: Optional[List[str]] = None,
        base_color: Optional[LogColor] = None,
        **kwargs,
    ):
        """
        Core logging method that handles message formatting and output.

        Args:
            level: Log level for this message
            message: Message template string
            tag: Tag for the message
            params: Parameters to format into the message
            colors: Color overrides for specific parameters
            boxes: Box overrides for specific parameters
            base_color: Base color for the entire message
        """
        if level.value < self.log_level.value:
            return

        # avoid conflict with rich formatting
        parsed_message = message.replace("[", "[[").replace("]", "]]")
        if params:
            # FIXME: If there are formatting strings in floating point format, 
            # this may result in colors and boxes not being applied properly.
            # such as {value:.2f}, the value is 0.23333 format it to 0.23,
            # but we replace("0.23333", "[color]0.23333[/color]")
            formatted_message = parsed_message.format(**params)
            for key, value in params.items():
                # value_str may discard `[` and `]`, so we need to replace it. 
                value_str = str(value).replace("[", "[[").replace("]", "]]")
                # check is need apply color
                if colors and key in colors:
                    color_str = f"[{colors[key]}]{value_str}[/{colors[key]}]"
                    formatted_message = formatted_message.replace(value_str, color_str)
                    value_str = color_str

                # check is need apply box
                if boxes and key in boxes:
                    formatted_message = formatted_message.replace(value_str,
                        create_box_message(value_str, type=str(level)))

        else:
            formatted_message = parsed_message

        # Construct the full log line
        color: LogColor = base_color or self.colors[level]
        log_line = f"[{color}]{self._format_tag(tag)} {self._get_icon(tag)} {formatted_message} [/{color}]"

        # Output to console if verbose
        if self.verbose or kwargs.get("force_verbose", False):
            self.console.print(log_line)

        # Write to file if configured
        self._write_to_file(log_line)