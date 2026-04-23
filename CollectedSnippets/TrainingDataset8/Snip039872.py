def elements(self) -> List[Element]:
        """Return the delta.new_element messages in our ForwardMsgQueue."""
        return [delta.new_element for delta in self.deltas()]