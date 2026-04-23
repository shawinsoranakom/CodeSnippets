def __init__(self):
        self._stacks: weakref.WeakKeyDictionary[
            threading.Thread, _HashStack
        ] = weakref.WeakKeyDictionary()