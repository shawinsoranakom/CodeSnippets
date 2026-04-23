def _get_element(self) -> Element:
        """Returns the most recent element in the DeltaGenerator queue"""
        return self.get_delta_from_queue().new_element