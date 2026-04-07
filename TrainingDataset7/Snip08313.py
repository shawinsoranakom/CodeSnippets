def __init__(
        self,
        servers,
        serializer=None,
        pool_class=None,
        parser_class=None,
        **options,
    ):
        import redis

        self._lib = redis
        self._servers = servers
        self._pools = {}

        self._client = self._lib.Redis

        if isinstance(pool_class, str):
            pool_class = import_string(pool_class)
        self._pool_class = pool_class or self._lib.ConnectionPool

        if isinstance(serializer, str):
            serializer = import_string(serializer)
        if callable(serializer):
            serializer = serializer()
        self._serializer = serializer or RedisSerializer()

        if isinstance(parser_class, str):
            parser_class = import_string(parser_class)
        parser_class = parser_class or self._lib.connection.DefaultParser

        version = django.get_version()
        if hasattr(self._lib, "DriverInfo"):
            driver_info = self._lib.DriverInfo().add_upstream_driver("django", version)
            driver_info_options = {"driver_info": driver_info}
        else:
            # DriverInfo is not available in this redis-py version.
            driver_info_options = {"lib_name": f"redis-py(django_v{version})"}

        self._pool_options = {
            "parser_class": parser_class,
            **driver_info_options,
            **options,
        }