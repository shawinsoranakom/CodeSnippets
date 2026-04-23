def __init__(self, failed_msg_str: Any):
        msg = self._get_message(failed_msg_str)
        super(MessageSizeError, self).__init__(msg)