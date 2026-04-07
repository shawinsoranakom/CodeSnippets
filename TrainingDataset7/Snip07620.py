def compute_msg(some_serialized_msg):
                return self._encode_parts(
                    [*some_serialized_msg, self.not_finished_json],
                    encode_empty=True,
                )