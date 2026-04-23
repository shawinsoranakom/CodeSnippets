def __init__(
        self,
        include_internal: bool = True,
        include_external: bool = False,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        concurrency: int = 10,
        timeout: int = 5,
        max_links: int = 100,
        query: Optional[str] = None,
        score_threshold: Optional[float] = None,
        verbose: bool = False
    ):
        """
        Initialize link extraction configuration.

        Args:
            include_internal: Whether to include same-domain links
            include_external: Whether to include different-domain links  
            include_patterns: List of glob patterns to include (e.g., ["*/docs/*", "*/api/*"])
            exclude_patterns: List of glob patterns to exclude (e.g., ["*/login*", "*/admin*"])
            concurrency: Number of links to process simultaneously
            timeout: Timeout in seconds for each link's head extraction
            max_links: Maximum number of links to process (prevents overload)
            query: Query string for BM25 contextual scoring (optional)
            score_threshold: Minimum relevance score to include links (0.0-1.0, optional)
            verbose: Show detailed progress during extraction
        """
        self.include_internal = include_internal
        self.include_external = include_external
        self.include_patterns = include_patterns
        self.exclude_patterns = exclude_patterns
        self.concurrency = concurrency
        self.timeout = timeout
        self.max_links = max_links
        self.query = query
        self.score_threshold = score_threshold
        self.verbose = verbose

        # Validation
        if concurrency <= 0:
            raise ValueError("concurrency must be positive")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if max_links <= 0:
            raise ValueError("max_links must be positive")
        if score_threshold is not None and not (0.0 <= score_threshold <= 1.0):
            raise ValueError("score_threshold must be between 0.0 and 1.0")
        if not include_internal and not include_external:
            raise ValueError("At least one of include_internal or include_external must be True")