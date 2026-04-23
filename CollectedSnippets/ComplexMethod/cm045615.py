def rest_connector(
    host: str | None = None,
    port: int | str | None = None,
    *,
    webserver: PathwayWebserver | None = None,
    route: str = "/",
    schema: type[pw.Schema] | None = None,
    methods: Sequence[str] = ("POST",),
    autocommit_duration_ms=1500,
    documentation: EndpointDocumentation = EndpointDocumentation(),
    keep_queries: bool | None = None,
    delete_completed_queries: bool | None = None,
    request_validator: Callable | None = None,
    cache_strategy: CacheStrategy | None = None,
) -> tuple[pw.Table, Callable]:
    """
    Runs a lightweight HTTP server and inputs a collection from the HTTP endpoint,
    configured by the parameters of this method.

    On the output, the method provides a table and a callable, which needs to accept
    the result table of the computation, which entries will be tracked and put into
    respective request's responses.

    Args:
        webserver: configuration object containing host and port information. You only
          need to create only one instance of this class per single host-port pair;
        route: route which will be listened to by the web server;
        schema: schema of the resulting table;
        methods: HTTP methods that this endpoint will accept;
        autocommit_duration_ms: the maximum time between two commits. Every
          autocommit_duration_ms milliseconds, the updates received by the connector are
          committed and pushed into Pathway's computation graph;
        keep_queries: whether to keep queries after processing; defaults to False. [deprecated]
        delete_completed_queries: whether to send a deletion entry after the query is processed.
          Allows to remove it from the system if it is stored by operators such as ``join`` or ``groupby``;
        request_validator: a callable that can verify requests. A return value of `None` accepts payload.
          Any other returned value is treated as error and used as the response. Any exception is
          caught and treated as validation failure.
        cache_strategy: one of available request caching strategies or None if no caching is required.
          If enabled, caches responses for the requests with the same ``schema``-defined payload.

    Returns:
        tuple: A tuple containing two elements. The table read and a ``response_writer``,
        a callable, where the result table should be provided. The ``id`` column of the result
        table must contain the primary keys of the objects from the input
        table and a ``result`` column, corresponding to the endpoint's return value.

    Example:

    Let's consider the following example: there is a collection of words that are
    received through HTTP REST endpoint `/uppercase` located at `127.0.0.1`, port `9999`.
    The Pathway program processes this table by converting these words to the upper case.
    This conversion result must be provided to the user on the output.

    Then, you can proceed with the following REST connector configuration code.

    First, the schema and the webserver object need to be created:

    >>> import pathway as pw
    >>> class WordsSchema(pw.Schema):
    ...     word: str
    ...
    >>>
    >>> webserver = pw.io.http.PathwayWebserver(host="127.0.0.1", port=9999)

    Then, the endpoint that inputs this collection can be configured:

    >>> words, response_writer = pw.io.http.rest_connector(
    ...     webserver=webserver,
    ...     route="/uppercase",
    ...     schema=WordsSchema,
    ... )

    Finally, you can define the logic that takes the input table `words`, calculates
    the result in the form of a table, and provides it for the endpoint's output:

    >>> uppercase_words = words.select(
    ...     query_id=words.id,
    ...     result=pw.apply(lambda x: x.upper(), pw.this.word)
    ... )
    >>> response_writer(uppercase_words)

    Please note that you don't need to create another web server object if you need to
    have more than one endpoint running on the same host and port. For example, if you need
    to create another endpoint that converts words to lower case, in the same way, you
    need to reuse the existing `webserver` object. That is, the configuration would start
    with:

    >>> words_for_lowercase, response_writer_for_lowercase = pw.io.http.rest_connector(
    ...     webserver=webserver,
    ...     route="/lowercase",
    ...     schema=WordsSchema,
    ... )
    """

    if delete_completed_queries is None:
        if keep_queries is None:
            warn(
                "delete_completed_queries arg of rest_connector should be set explicitly."
                + " It will soon be required."
            )
            delete_completed_queries = True
        else:
            warn(
                "DEPRECATED: keep_queries arg of rest_connector is deprecated,"
                + " use delete_completed_queries with an opposite meaning instead."
            )
            delete_completed_queries = not keep_queries

    if schema is None:
        format = "raw"
        schema = pw.schema_builder({"query": pw.column_definition()})
    else:
        format = "custom"

    if webserver is None:
        if host is None or port is None:
            raise ValueError(
                "If webserver object isn't specified, host and port must be present"
            )
        if isinstance(port, str):
            port = int(port)
        warn(
            "The `host` and `port` arguments are deprecated. Please use `webserver` "
            "instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        webserver = PathwayWebserver(host, port)
    else:
        if host is not None or port is not None:
            raise ValueError(
                "If webserver object is specified, host and port shouldn't be set"
            )

    input_table = io.python.read(
        subject=RestServerSubject(
            webserver=webserver,
            route=route,
            methods=methods,
            schema=schema,
            delete_completed_queries=delete_completed_queries,
            format=format,
            request_validator=request_validator,
            documentation=documentation,
            cache_strategy=cache_strategy,
        ),
        schema=schema,
        format="json",
        autocommit_duration_ms=autocommit_duration_ms,
    )

    return input_table, webserver._get_response_writer(delete_completed_queries)