def enable_builtins(self, **kwargs) -> None:
        """
        Enable and register built-in converters.
        Built-in converters are enabled by default.
        This method should only be called once, if built-ins were initially disabled.
        """
        if not self._builtins_enabled:
            # TODO: Move these into converter constructors
            self._llm_client = kwargs.get("llm_client")
            self._llm_model = kwargs.get("llm_model")
            self._llm_prompt = kwargs.get("llm_prompt")
            self._exiftool_path = kwargs.get("exiftool_path")
            self._style_map = kwargs.get("style_map")

            if self._exiftool_path is None:
                self._exiftool_path = os.getenv("EXIFTOOL_PATH")

            # Still none? Check well-known paths
            if self._exiftool_path is None:
                candidate = shutil.which("exiftool")
                if candidate:
                    candidate = os.path.abspath(candidate)
                    if any(
                        d == os.path.dirname(candidate)
                        for d in [
                            "/usr/bin",
                            "/usr/local/bin",
                            "/opt",
                            "/opt/bin",
                            "/opt/local/bin",
                            "/opt/homebrew/bin",
                            "C:\\Windows\\System32",
                            "C:\\Program Files",
                            "C:\\Program Files (x86)",
                        ]
                    ):
                        self._exiftool_path = candidate

            # Register converters for successful browsing operations
            # Later registrations are tried first / take higher priority than earlier registrations
            # To this end, the most specific converters should appear below the most generic converters
            self.register_converter(
                PlainTextConverter(), priority=PRIORITY_GENERIC_FILE_FORMAT
            )
            self.register_converter(
                ZipConverter(markitdown=self), priority=PRIORITY_GENERIC_FILE_FORMAT
            )
            self.register_converter(
                HtmlConverter(), priority=PRIORITY_GENERIC_FILE_FORMAT
            )
            self.register_converter(RssConverter())
            self.register_converter(WikipediaConverter())
            self.register_converter(YouTubeConverter())
            self.register_converter(BingSerpConverter())
            self.register_converter(DocxConverter())
            self.register_converter(XlsxConverter())
            self.register_converter(XlsConverter())
            self.register_converter(PptxConverter())
            self.register_converter(AudioConverter())
            self.register_converter(ImageConverter())
            self.register_converter(IpynbConverter())
            self.register_converter(PdfConverter())
            self.register_converter(OutlookMsgConverter())
            self.register_converter(EpubConverter())
            self.register_converter(CsvConverter())

            # Register Document Intelligence converter at the top of the stack if endpoint is provided
            docintel_endpoint = kwargs.get("docintel_endpoint")
            if docintel_endpoint is not None:
                docintel_args: Dict[str, Any] = {}
                docintel_args["endpoint"] = docintel_endpoint

                docintel_credential = kwargs.get("docintel_credential")
                if docintel_credential is not None:
                    docintel_args["credential"] = docintel_credential

                docintel_types = kwargs.get("docintel_file_types")
                if docintel_types is not None:
                    docintel_args["file_types"] = docintel_types

                docintel_version = kwargs.get("docintel_api_version")
                if docintel_version is not None:
                    docintel_args["api_version"] = docintel_version

                self.register_converter(
                    DocumentIntelligenceConverter(**docintel_args),
                )

            self._builtins_enabled = True
        else:
            warn("Built-in converters are already enabled.", RuntimeWarning)