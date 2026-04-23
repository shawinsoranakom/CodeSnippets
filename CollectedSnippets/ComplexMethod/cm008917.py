def __init__(
        self,
        headers_to_split_on: list[tuple[str, str]],
        *,
        max_chunk_size: int = 1000,
        chunk_overlap: int = 0,
        separators: list[str] | None = None,
        elements_to_preserve: list[str] | None = None,
        preserve_links: bool = False,
        preserve_images: bool = False,
        preserve_videos: bool = False,
        preserve_audio: bool = False,
        custom_handlers: dict[str, Callable[[Tag], str]] | None = None,
        stopword_removal: bool = False,
        stopword_lang: str = "english",
        normalize_text: bool = False,
        external_metadata: dict[str, str] | None = None,
        allowlist_tags: list[str] | None = None,
        denylist_tags: list[str] | None = None,
        preserve_parent_metadata: bool = False,
        keep_separator: bool | Literal["start", "end"] = True,
    ) -> None:
        """Initialize splitter.

        Args:
            headers_to_split_on: HTML headers (e.g., `h1`, `h2`) that define content
                sections.
            max_chunk_size: Maximum size for each chunk, with allowance for exceeding
                this limit to preserve semantics.
            chunk_overlap: Number of characters to overlap between chunks to ensure
                contextual continuity.
            separators: Delimiters used by `RecursiveCharacterTextSplitter` for
                further splitting.
            elements_to_preserve: HTML tags (e.g., `table`, `ul`) to remain
                intact during splitting.
            preserve_links: Converts `a` tags to Markdown links (`[text](url)`).
            preserve_images: Converts `img` tags to Markdown images (`![alt](src)`).
            preserve_videos: Converts `video` tags to Markdown video links
                (`![video](src)`).
            preserve_audio: Converts `audio` tags to Markdown audio links
                (`![audio](src)`).
            custom_handlers: Optional custom handlers for specific HTML tags, allowing
                tailored extraction or processing.
            stopword_removal: Optionally remove stopwords from the text.
            stopword_lang: The language of stopwords to remove.
            normalize_text: Optionally normalize text (e.g., lowercasing, removing
                punctuation).
            external_metadata: Additional metadata to attach to the Document objects.
            allowlist_tags: Only these tags will be retained in the HTML.
            denylist_tags: These tags will be removed from the HTML.
            preserve_parent_metadata: Whether to pass through parent document metadata
                to split documents when calling
                `transform_documents/atransform_documents()`.
            keep_separator: Whether separators should be at the beginning of a chunk, at
                the end, or not at all.

        Raises:
            ImportError: If BeautifulSoup or NLTK (when stopword removal is enabled)
                is not installed.
        """
        if not _HAS_BS4:
            msg = (
                "Could not import BeautifulSoup. "
                "Please install it with 'pip install bs4'."
            )
            raise ImportError(msg)

        self._headers_to_split_on = sorted(headers_to_split_on)
        self._max_chunk_size = max_chunk_size
        self._elements_to_preserve = elements_to_preserve or []
        self._preserve_links = preserve_links
        self._preserve_images = preserve_images
        self._preserve_videos = preserve_videos
        self._preserve_audio = preserve_audio
        self._custom_handlers = custom_handlers or {}
        self._stopword_removal = stopword_removal
        self._stopword_lang = stopword_lang
        self._normalize_text = normalize_text
        self._external_metadata = external_metadata or {}
        self._allowlist_tags = allowlist_tags
        self._preserve_parent_metadata = preserve_parent_metadata
        self._keep_separator = keep_separator
        if allowlist_tags:
            self._allowlist_tags = list(
                set(allowlist_tags + [header[0] for header in headers_to_split_on])
            )
        self._denylist_tags = denylist_tags
        if denylist_tags:
            self._denylist_tags = [
                tag
                for tag in denylist_tags
                if tag not in [header[0] for header in headers_to_split_on]
            ]
        if separators:
            self._recursive_splitter = RecursiveCharacterTextSplitter(
                separators=separators,
                keep_separator=keep_separator,
                chunk_size=max_chunk_size,
                chunk_overlap=chunk_overlap,
            )
        else:
            self._recursive_splitter = RecursiveCharacterTextSplitter(
                keep_separator=keep_separator,
                chunk_size=max_chunk_size,
                chunk_overlap=chunk_overlap,
            )

        if self._stopword_removal:
            if not _HAS_NLTK:
                msg = (
                    "Could not import nltk. Please install it with 'pip install nltk'."
                )
                raise ImportError(msg)
            nltk.download("stopwords")
            self._stopwords = set(nltk.corpus.stopwords.words(self._stopword_lang))