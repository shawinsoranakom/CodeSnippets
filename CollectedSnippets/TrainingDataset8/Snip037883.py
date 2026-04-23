def __init__(self):
        self._queue: List[ForwardMsg] = []
        # A mapping of (delta_path -> _queue.indexof(msg)) for each
        # Delta message in the queue. We use this for coalescing
        # redundant outgoing Deltas (where a newer Delta supersedes
        # an older Delta, with the same delta_path, that's still in the
        # queue).
        self._delta_index_map: Dict[Tuple[int, ...], int] = dict()