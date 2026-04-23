def test_data_message_content_format_inconsistency(self):
        """Document the Data.to_lc_message() content format inconsistency and its solution.

        DESIGN ISSUE DOCUMENTED: Data.to_lc_message() produces different content formats:
        - User messages (HumanMessage): content = [{"type": "text", "text": "..."}] (list format)
        - Assistant messages (AIMessage): content = "text" (string format)
        ROOT CAUSE: lfx/schema/data.py lines 175-189 implement different serialization:
        - USER sender: HumanMessage(content=[{"type": "text", "text": text}])  # Always list
        - AI sender: AIMessage(content=text)  # Always string
        SOLUTION IMPLEMENTED:
        1. normalize_message_content() helper function handles both formats
        2. NormalizedInputProxy in ALTKAgentComponent intercepts inconsistent content
        3. Proxy automatically converts list format to string when needed
        """
        from lfx.schema.data import Data

        user_data = Data(data={"text": "user message", "sender": "User"})
        assistant_data = Data(data={"text": "assistant message", "sender": "Assistant"})

        user_message = user_data.to_lc_message()
        assistant_message = assistant_data.to_lc_message()

        # DOCUMENT THE INCONSISTENCY (still exists in core Data class)
        assert user_message.content == [{"type": "text", "text": "user message"}]
        assert isinstance(user_message.content, list)
        assert assistant_message.content == "assistant message"
        assert isinstance(assistant_message.content, str)

        # DEMONSTRATE THE SOLUTION: normalize_message_content handles both formats
        from lfx.base.agents.altk_base_agent import normalize_message_content

        normalized_user = normalize_message_content(user_message)
        normalized_assistant = normalize_message_content(assistant_message)

        # Both are now consistent string format
        assert normalized_user == "user message"
        assert normalized_assistant == "assistant message"
        assert isinstance(normalized_user, str)
        assert isinstance(normalized_assistant, str)