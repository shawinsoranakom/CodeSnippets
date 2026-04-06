def __init__(self, cm: AbstractContextManager[_T]) -> None:
        self._cm = cm