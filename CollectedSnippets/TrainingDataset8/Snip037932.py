def __init__(self):
        self._stack: collections.OrderedDict[int, List[Any]] = collections.OrderedDict()

        # The reason why we're doing this hashing, for debug purposes.
        self.hash_reason: Optional[HashReason] = None

        # Either a function or a code block, depending on whether the reason is
        # due to hashing part of a function (i.e. body, args, output) or an
        # st.Cache codeblock.
        self.hash_source: Optional[Callable[..., Any]] = None