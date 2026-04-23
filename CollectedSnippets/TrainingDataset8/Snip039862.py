def _assert_forward_msgs(
        self, scriptrunner: "TestScriptRunner", messages: List[ForwardMsg]
    ) -> None:
        """Assert that the ScriptRunner's ForwardMsgQueue contains the
        given list of ForwardMsgs.
        """
        self.assertEqual(messages, scriptrunner.forward_msgs())