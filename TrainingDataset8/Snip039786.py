def is_data_msg_cached() -> bool:
                return (
                    self.runtime._message_cache.get_message(data_msg.hash) is not None
                )