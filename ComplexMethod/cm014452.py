def _remove_biggest_key(self):
        biggest_key = None
        biggest_size = 0
        result_to_yield = None
        for findkey in self.buffer_elements:
            if len(self.buffer_elements[findkey]) > biggest_size:
                biggest_size = len(self.buffer_elements[findkey])
                biggest_key = findkey

        if (
            self.guaranteed_group_size is not None
            and biggest_size < self.guaranteed_group_size
            and not self.drop_remaining
        ):
            raise RuntimeError(
                "Failed to group items", str(self.buffer_elements[biggest_key])
            )

        if (
            self.guaranteed_group_size is None
            or biggest_size >= self.guaranteed_group_size
        ):
            result_to_yield = self.buffer_elements[biggest_key]

        self.curr_buffer_size -= biggest_size
        del self.buffer_elements[biggest_key]

        return result_to_yield