def __init__(
        self,
        prompt,
        style="precise",
        content_type="text",
        cookie_file=0,
        echo=True,
        echo_prompt=False,
    ):
        """
        Arguments:

        prompt: Text to enter into Bing Chat
        style: creative, balanced, or precise
        content_type: "text" for Bing Chat; "image" for Dall-e
        cookie_file: Path, filepath string, or index (int) to list of cookie paths
        echo: Print something to confirm request made
        echo_prompt: Print confirmation of the evaluated prompt
        """
        self.index = []
        self.request_count = {}
        self.image_dirpath = Path("./").resolve()
        Cookie.import_data()
        self.index += [self]
        self.prompt = prompt
        files = Cookie.files()
        if isinstance(cookie_file, int):
            index = cookie_file if cookie_file < len(files) else 0
        else:
            if not isinstance(cookie_file, (str, Path)):
                message = "'cookie_file' must be an int, str, or Path object"
                raise TypeError(message)
            cookie_file = Path(cookie_file)
            if cookie_file in files():  # Supplied filepath IS in Cookie.dirpath
                index = files.index(cookie_file)
            else:  # Supplied filepath is NOT in Cookie.dirpath
                if cookie_file.is_file():
                    Cookie.dirpath = cookie_file.parent.resolve()
                if cookie_file.is_dir():
                    Cookie.dirpath = cookie_file.resolve()
                index = 0
        Cookie.current_file_index = index
        if content_type == "text":
            self.style = style
            self.log_and_send_query(echo, echo_prompt)
        if content_type == "image":
            self.create_image()