def __init__(self):
        self._components = {}  # type: Dict[str, CustomComponent]
        self._lock = threading.Lock()