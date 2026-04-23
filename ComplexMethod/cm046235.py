def __init__(self, source: str, channels: int = 3):
        """Initialize screenshot capture with specified screen and region parameters.

        Args:
            source (str): Screen capture source string in format "screen_num left top width height".
            channels (int): Number of image channels (1 for grayscale, 3 for color).
        """
        check_requirements("mss")
        import mss

        source, *params = source.split()
        self.screen, left, top, width, height = 0, None, None, None, None  # default to full screen 0
        if len(params) == 1:
            self.screen = int(params[0])
        elif len(params) == 4:
            left, top, width, height = (int(x) for x in params)
        elif len(params) == 5:
            self.screen, left, top, width, height = (int(x) for x in params)
        self.mode = "stream"
        self.frame = 0
        self.sct = mss.mss()
        self.bs = 1
        self.fps = 30
        self.cv2_flag = cv2.IMREAD_GRAYSCALE if channels == 1 else cv2.IMREAD_COLOR  # grayscale or color (BGR)

        # Parse monitor shape
        monitor = self.sct.monitors[self.screen]
        self.top = monitor["top"] if top is None else (monitor["top"] + top)
        self.left = monitor["left"] if left is None else (monitor["left"] + left)
        self.width = width or monitor["width"]
        self.height = height or monitor["height"]
        self.monitor = {"left": self.left, "top": self.top, "width": self.width, "height": self.height}