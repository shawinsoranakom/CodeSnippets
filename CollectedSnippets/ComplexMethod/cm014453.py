def __iter__(self):
        for x in self.datapipe:
            key = self.group_key_fn(x)

            self.buffer_elements[key].append(x)
            self.curr_buffer_size += 1

            if self.group_size is not None and self.group_size == len(
                self.buffer_elements[key]
            ):
                result: DataChunk[Any] = self.wrapper_class(self.buffer_elements[key])
                yield (key, result) if self.keep_key else result
                self.curr_buffer_size -= len(self.buffer_elements[key])
                del self.buffer_elements[key]

            if self.curr_buffer_size == self.max_buffer_size:
                result_to_yield = self._remove_biggest_key()
                if result_to_yield is not None:
                    result = self.wrapper_class(result_to_yield)
                    yield (key, result) if self.keep_key else result

        for key in tuple(self.buffer_elements.keys()):
            result = self.wrapper_class(self.buffer_elements.pop(key))
            self.curr_buffer_size -= len(result)
            yield (key, result) if self.keep_key else result