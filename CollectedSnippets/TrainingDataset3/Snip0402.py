def format(self, record: logging.LogRecord) -> str:
       # Make sure `msg` is a string
       if not hasattr(record, "msg"):
           record.msg = ""
      elif type(record.msg) is not str:
            record.msg = str(record.msg)

      # Determine default color based on error level
      level_color = ""
      if record.levelno in self.LEVEL_COLOR_MAP:
          level_color = self.LEVEL_COLOR_MAP[record.levelno]
          record.levelname = f"{level_color}{record.levelname}{Style.RESET_ALL}"

        # Determine color for message
      color = getattr(record, "color", level_color)
      color_is_specified = hasattr(record, "color")

        # Don't color INFO messages unless the color is explicitly specified.
      if color and (record.levelno != logging.INFO or color_is_specified):
          record.msg = f"{color}{record.msg}{Style.RESET_ALL}"

      return super().format(record)
