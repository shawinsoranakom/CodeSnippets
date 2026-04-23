def __init__(self, cache_type: CacheType):
        self._cached_message_stack: List[List[MsgData]] = []
        self._seen_dg_stack: List[Set[str]] = []
        self._most_recent_messages: List[MsgData] = []
        self._registered_metadata: Optional[WidgetMetadata[Any]] = None
        self._media_data: List[MediaMsgData] = []
        self._cache_type = cache_type
        self._allow_widgets: int = 0