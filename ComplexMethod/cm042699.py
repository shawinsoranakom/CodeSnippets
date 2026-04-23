def __init__(
        self,
        url: str,
        callback: CallbackT | None = None,
        method: str = "GET",
        headers: Mapping[AnyStr, Any] | Iterable[tuple[AnyStr, Any]] | None = None,
        body: bytes | str | None = None,
        cookies: CookiesT | None = None,
        meta: dict[str, Any] | None = None,
        encoding: str = "utf-8",
        priority: int = 0,
        dont_filter: bool = False,
        errback: Callable[[Failure], Any] | None = None,
        flags: list[str] | None = None,
        cb_kwargs: dict[str, Any] | None = None,
    ) -> None:
        self._encoding: str = encoding  # this one has to be set first
        self.method: str = str(method).upper()
        self._set_url(url)
        self._set_body(body)
        if not isinstance(priority, int):
            raise TypeError(f"Request priority not an integer: {priority!r}")

        #: Default: ``0``
        #:
        #: Value that the :ref:`scheduler <topics-scheduler>` may use for
        #: request prioritization.
        #:
        #: Built-in schedulers prioritize requests with a higher priority
        #: value.
        #:
        #: Negative values are allowed.
        self.priority: int = priority

        if not (callable(callback) or callback is None):
            raise TypeError(
                f"callback must be a callable, got {type(callback).__name__}"
            )
        if not (callable(errback) or errback is None):
            raise TypeError(f"errback must be a callable, got {type(errback).__name__}")

        #: :class:`~collections.abc.Callable` to parse the
        #: :class:`~scrapy.http.Response` to this request once received.
        #:
        #: The callable must expect the response as its first parameter, and
        #: support any additional keyword arguments set through
        #: :attr:`cb_kwargs`.
        #:
        #: In addition to an arbitrary callable, the following values are also
        #: supported:
        #:
        #: -   ``None`` (default), which indicates that the
        #:     :meth:`~scrapy.Spider.parse` method of the spider must be used.
        #:
        #: -   :func:`~scrapy.http.request.NO_CALLBACK`.
        #:
        #: If an unhandled exception is raised during request or response
        #: processing, i.e. by a :ref:`spider middleware
        #: <topics-spider-middleware>`, :ref:`downloader middleware
        #: <topics-downloader-middleware>` or download handler
        #: (:setting:`DOWNLOAD_HANDLERS`), :attr:`errback` is called instead.
        #:
        #: .. tip::
        #:     :class:`~scrapy.spidermiddlewares.httperror.HttpErrorMiddleware`
        #:     raises exceptions for non-2xx responses by default, sending them
        #:     to the :attr:`errback` instead.
        #:
        #: .. seealso::
        #:     :ref:`topics-request-response-ref-request-callback-arguments`
        self.callback: CallbackT | None = callback

        #: :class:`~collections.abc.Callable` to handle exceptions raised
        #: during request or response processing.
        #:
        #: The callable must expect a :exc:`~twisted.python.failure.Failure` as
        #: its first parameter.
        #:
        #: .. seealso:: :ref:`topics-request-response-ref-errbacks`
        self.errback: Callable[[Failure], Any] | None = errback

        self._cookies: CookiesT | None = cookies or None
        self._headers: Headers | None = (
            Headers(headers, encoding=encoding) if headers else None
        )

        #: Whether this request may be filtered out by :ref:`components
        #: <topics-components>` that support filtering out requests (``False``,
        #: default), or those components should not filter out this request
        #: (``True``).
        #:
        #: The following built-in components check this attribute:
        #:
        #: -   The :ref:`scheduler <topics-scheduler>` uses it to skip
        #:     duplicate request filtering (see
        #:     :setting:`DUPEFILTER_CLASS`). When set to ``True``, the
        #:     request is not checked against the duplicate filter,
        #:     allowing requests that would otherwise be considered duplicates
        #:     to be scheduled multiple times.
        #: -   :class:`~scrapy.downloadermiddlewares.offsite.OffsiteMiddleware`
        #:     uses it to allow requests to domains not in
        #:     :attr:`~scrapy.Spider.allowed_domains`. To skip only the offsite
        #:     filter without affecting other components, consider using the
        #:     :reqmeta:`allow_offsite` request meta key instead.
        #:
        #: Third-party components may also use this attribute to decide whether
        #: to filter out a request.
        #:
        #: When defining the start URLs of a spider through
        #: :attr:`~scrapy.Spider.start_urls`, this attribute is enabled by
        #: default. See :meth:`~scrapy.Spider.start`.
        self.dont_filter: bool = dont_filter

        self._meta: dict[str, Any] | None = dict(meta) if meta else None
        self._cb_kwargs: dict[str, Any] | None = dict(cb_kwargs) if cb_kwargs else None
        self._flags: list[str] | None = list(flags) if flags else None