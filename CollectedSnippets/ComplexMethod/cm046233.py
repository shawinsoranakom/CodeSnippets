def __init__(self, sources: str = "file.streams", vid_stride: int = 1, buffer: bool = False, channels: int = 3):
        """Initialize stream loader for multiple video sources, supporting various stream types.

        Args:
            sources (str): Path to streams file or single stream URL.
            vid_stride (int): Video frame-rate stride.
            buffer (bool): Whether to buffer input streams.
            channels (int): Number of image channels (1 for grayscale, 3 for color).
        """
        torch.backends.cudnn.benchmark = True  # faster for fixed-size inference
        self.buffer = buffer  # buffer input streams
        self.running = True  # running flag for Thread
        self.mode = "stream"
        self.vid_stride = vid_stride  # video frame-rate stride
        self.cv2_flag = cv2.IMREAD_GRAYSCALE if channels == 1 else cv2.IMREAD_COLOR  # grayscale or color (BGR)

        sources = Path(sources).read_text().rsplit() if os.path.isfile(sources) else [sources]
        n = len(sources)
        self.bs = n
        self.fps = [0] * n  # frames per second
        self.frames = [0] * n
        self.threads = [None] * n
        self.caps = [None] * n  # video capture objects
        self.imgs = [[] for _ in range(n)]  # images
        self.shape = [[] for _ in range(n)]  # image shapes
        self.sources = [ops.clean_str(x).replace(os.sep, "_") for x in sources]  # clean source names for later
        for i, s in enumerate(sources):  # index, source
            # Start thread to read frames from video stream
            st = f"{i + 1}/{n}: {s}... "
            if urllib.parse.urlparse(s).hostname in {"www.youtube.com", "youtube.com", "youtu.be"}:  # YouTube video
                # YouTube format i.e. 'https://www.youtube.com/watch?v=Jsn8D3aC840' or 'https://youtu.be/Jsn8D3aC840'
                s = get_best_youtube_url(s)
            s = int(s) if s.isnumeric() else s  # i.e. s = '0' local webcam
            if s == 0 and (IS_COLAB or IS_KAGGLE):
                raise NotImplementedError(
                    "'source=0' webcam not supported in Colab and Kaggle notebooks. "
                    "Try running 'source=0' in a local environment."
                )
            self.caps[i] = cv2.VideoCapture(s)  # store video capture object
            if not self.caps[i].isOpened():
                raise ConnectionError(f"{st}Failed to open {s}")
            w = int(self.caps[i].get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(self.caps[i].get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = self.caps[i].get(cv2.CAP_PROP_FPS)  # warning: may return 0 or nan
            self.frames[i] = max(int(self.caps[i].get(cv2.CAP_PROP_FRAME_COUNT)), 0) or float(
                "inf"
            )  # infinite stream fallback
            self.fps[i] = max((fps if math.isfinite(fps) else 0) % 100, 0) or 30  # 30 FPS fallback

            success, im = self.caps[i].read()  # guarantee first frame
            im = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)[..., None] if self.cv2_flag == cv2.IMREAD_GRAYSCALE else im
            if not success or im is None:
                raise ConnectionError(f"{st}Failed to read images from {s}")
            self.imgs[i].append(im)
            self.shape[i] = im.shape
            self.threads[i] = Thread(target=self.update, args=([i, self.caps[i], s]), daemon=True)
            LOGGER.info(f"{st}Success ✅ ({self.frames[i]} frames of shape {w}x{h} at {self.fps[i]:.2f} FPS)")
            self.threads[i].start()
        LOGGER.info("")