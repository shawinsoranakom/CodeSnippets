def __init__(self, path: str | Path | list, batch: int = 1, vid_stride: int = 1, channels: int = 3):
        """Initialize dataloader for images and videos, supporting various input formats.

        Args:
            path (str | Path | list): Path to images/videos, directory, or list of paths.
            batch (int): Batch size for processing.
            vid_stride (int): Video frame-rate stride.
            channels (int): Number of image channels (1 for grayscale, 3 for color).
        """
        parent = None
        if isinstance(path, str) and Path(path).suffix in {".txt", ".csv"}:  # txt/csv file with source paths
            parent, content = Path(path).parent, Path(path).read_text()
            path = content.splitlines() if Path(path).suffix == ".txt" else content.split(",")  # list of sources
            path = [p.strip() for p in path]
        files = []
        for p in sorted(path) if isinstance(path, (list, tuple)) else [path]:
            a = str(Path(p).absolute())  # do not use .resolve() https://github.com/ultralytics/ultralytics/issues/2912
            if "*" in a:
                files.extend(sorted(glob.glob(a, recursive=True)))  # glob
            elif os.path.isdir(a):
                files.extend(sorted(glob.glob(os.path.join(a, "*.*"))))  # dir
            elif os.path.isfile(a):
                files.append(a)  # files (absolute or relative to CWD)
            elif parent and (parent / p).is_file():
                files.append(str((parent / p).absolute()))  # files (relative to *.txt file parent)
            else:
                raise FileNotFoundError(f"{p} does not exist")

        # Define files as images or videos
        images, videos = [], []
        for f in files:
            suffix = f.rpartition(".")[-1].lower()  # Get file extension without the dot and lowercase
            if suffix in IMG_FORMATS:
                images.append(f)
            elif suffix in VID_FORMATS:
                videos.append(f)
        ni, nv = len(images), len(videos)

        self.files = images + videos
        self.nf = ni + nv  # number of files
        self.ni = ni  # number of images
        self.video_flag = [False] * ni + [True] * nv
        self.mode = "video" if ni == 0 else "image"  # default to video if no images
        self.vid_stride = vid_stride  # video frame-rate stride
        self.bs = batch
        self.cv2_flag = cv2.IMREAD_GRAYSCALE if channels == 1 else cv2.IMREAD_COLOR  # grayscale or color (BGR)
        if any(videos):
            self._new_video(videos[0])  # new video
        else:
            self.cap = None
        if self.nf == 0:
            raise FileNotFoundError(f"No images or videos found in {p}. {FORMATS_HELP_MSG}")