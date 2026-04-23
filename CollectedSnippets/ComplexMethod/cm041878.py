def handle_undo(self, arguments):
    # Removes all messages after the most recent user entry (and the entry itself).
    # Therefore user can jump back to the latest point of conversation.
    # Also gives a visual representation of the messages removed.

    if len(self.messages) == 0:
        return
    # Find the index of the last 'role': 'user' entry
    last_user_index = None
    for i, message in enumerate(self.messages):
        if message.get("role") == "user":
            last_user_index = i

    removed_messages = []

    # Remove all messages after the last 'role': 'user'
    if last_user_index is not None:
        removed_messages = self.messages[last_user_index:]
        self.messages = self.messages[:last_user_index]

    print("")  # Aesthetics.

    # Print out a preview of what messages were removed.
    for message in removed_messages:
        if "content" in message and message["content"] != None:
            self.display_message(
                f"**Removed message:** `\"{message['content'][:30]}...\"`"
            )
        elif "function_call" in message:
            self.display_message(
                f"**Removed codeblock**"
            )  # TODO: Could add preview of code removed here.

    print("")