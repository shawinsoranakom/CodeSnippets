def _store(self, messages, response, remove_oldest=True, *args, **kwargs):
        """
        Store the messages to a cookie and return a list of any messages which
        could not be stored.

        If the encoded data is larger than ``max_cookie_size``, remove
        messages until the data fits (these are the messages which are
        returned), and add the not_finished sentinel value to indicate as much.
        """
        unstored_messages = []
        serialized_messages = MessagePartSerializer().dumps(messages)
        encoded_data = self._encode_parts(serialized_messages)
        if self.max_cookie_size:
            # data is going to be stored eventually by SimpleCookie, which
            # adds its own overhead, which we must account for.
            cookie = SimpleCookie()  # create outside the loop

            def is_too_large_for_cookie(data):
                return data and len(cookie.value_encode(data)[1]) > self.max_cookie_size

            def compute_msg(some_serialized_msg):
                return self._encode_parts(
                    [*some_serialized_msg, self.not_finished_json],
                    encode_empty=True,
                )

            if is_too_large_for_cookie(encoded_data):
                if remove_oldest:
                    idx = bisect_keep_right(
                        serialized_messages,
                        fn=lambda m: is_too_large_for_cookie(compute_msg(m)),
                    )
                    unstored_messages = messages[:idx]
                    encoded_data = compute_msg(serialized_messages[idx:])
                else:
                    idx = bisect_keep_left(
                        serialized_messages,
                        fn=lambda m: is_too_large_for_cookie(compute_msg(m)),
                    )
                    unstored_messages = messages[idx:]
                    encoded_data = compute_msg(serialized_messages[:idx])

        self._update_cookie(encoded_data, response)
        return unstored_messages