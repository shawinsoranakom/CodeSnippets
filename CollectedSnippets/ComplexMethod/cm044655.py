def open(
        self,
        file: Union[str, "PathLike[str]", bytes],
        mode: Union[Literal["rb"], Literal["rt"], Literal["r"]] = "r",
        buffering: int = -1,
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
        *,
        total: Optional[int] = None,
        task_id: Optional[TaskID] = None,
        description: str = "Reading...",
    ) -> Union[BinaryIO, TextIO]:
        """Track progress while reading from a binary file.

        Args:
            path (Union[str, PathLike[str]]): The path to the file to read.
            mode (str): The mode to use to open the file. Only supports "r", "rb" or "rt".
            buffering (int): The buffering strategy to use, see :func:`io.open`.
            encoding (str, optional): The encoding to use when reading in text mode, see :func:`io.open`.
            errors (str, optional): The error handling strategy for decoding errors, see :func:`io.open`.
            newline (str, optional): The strategy for handling newlines in text mode, see :func:`io.open`.
            total (int, optional): Total number of bytes to read. If none given, os.stat(path).st_size is used.
            task_id (TaskID): Task to track. Default is new task.
            description (str, optional): Description of task, if new task is created.

        Returns:
            BinaryIO: A readable file-like object in binary mode.

        Raises:
            ValueError: When an invalid mode is given.
        """
        # normalize the mode (always rb, rt)
        _mode = "".join(sorted(mode, reverse=False))
        if _mode not in ("br", "rt", "r"):
            raise ValueError(f"invalid mode {mode!r}")

        # patch buffering to provide the same behaviour as the builtin `open`
        line_buffering = buffering == 1
        if _mode == "br" and buffering == 1:
            warnings.warn(
                "line buffering (buffering=1) isn't supported in binary mode, the default buffer size will be used",
                RuntimeWarning,
            )
            buffering = -1
        elif _mode in ("rt", "r"):
            if buffering == 0:
                raise ValueError("can't have unbuffered text I/O")
            elif buffering == 1:
                buffering = -1

        # attempt to get the total with `os.stat`
        if total is None:
            total = stat(file).st_size

        # update total of task or create new task
        if task_id is None:
            task_id = self.add_task(description, total=total)
        else:
            self.update(task_id, total=total)

        # open the file in binary mode,
        handle = io.open(file, "rb", buffering=buffering)
        reader = _Reader(handle, self, task_id, close_handle=True)

        # wrap the reader in a `TextIOWrapper` if text mode
        if mode in ("r", "rt"):
            return io.TextIOWrapper(
                reader,
                encoding=encoding,
                errors=errors,
                newline=newline,
                line_buffering=line_buffering,
            )

        return reader