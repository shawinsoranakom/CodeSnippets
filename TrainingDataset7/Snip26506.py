def test_safedata(self):
        """
        A message containing SafeData keeps its safe status when retrieved from
        the message storage.
        """
        storage = self.get_storage()
        message = Message(constants.DEBUG, mark_safe("<b>Hello Django!</b>"))
        set_session_data(storage, [message])
        self.assertIsInstance(list(storage)[0].message, SafeData)