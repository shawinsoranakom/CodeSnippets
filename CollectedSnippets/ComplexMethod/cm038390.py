def update_stream_state_pre_v11_tokenizer(self):
        while True:
            (prefix, event, value) = yield

            if prefix == "item" and event == "start_map":
                self.streaming_state = StreamingState.WAITING_FOR_TOOL_KEY
            if prefix == "item" and event == "map_key" and value == "name":
                self.streaming_state = StreamingState.PARSING_NAME
            if prefix == "item.name" and event == "string":
                self.current_tool_name = value
                self.streaming_state = StreamingState.PARSING_NAME_COMPLETED
            if prefix == "item" and event == "map_key" and value == "arguments":
                self.streaming_state = StreamingState.WAITING_FOR_ARGUMENTS_START
            if prefix == "item.arguments" and event == "start_map":
                self.streaming_state = StreamingState.PARSING_ARGUMENTS
            if prefix == "item.arguments" and event == "end_map":
                self.streaming_state = StreamingState.PARSING_ARGUMENTS_COMPLETED
            if prefix == "item" and event == "end_map":
                self.streaming_state = StreamingState.TOOL_COMPLETE
            if prefix == "" and event == "end_array":
                self.streaming_state = StreamingState.ALL_TOOLS_COMPLETE