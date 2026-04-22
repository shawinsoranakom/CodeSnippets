def keys(self) -> KeysView[str]:
        return KeysView(self.states)