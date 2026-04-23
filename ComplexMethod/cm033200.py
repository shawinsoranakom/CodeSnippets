def drop_chat_session(self, command):
        if self.server_type != "user":
            print("This command is only allowed in USER mode")
        chat_name = command["chat_name"]
        session_id = command["session_id"]
        dialog_id = self._get_chat_id_by_name(chat_name)
        if dialog_id is None:
            return
        sessions = self._list_chat_sessions(dialog_id)
        if sessions is None:
            return
        to_drop_session_ids = []
        for session in sessions:
            if session["id"] == session_id:
                to_drop_session_ids.append(session["id"])
        if not to_drop_session_ids:
            print(f"Chat session '{session_id}' not found in chat '{chat_name}'")
            return
        payload = {"ids": to_drop_session_ids}
        response = self.http_client.request("DELETE", f"/chats/{dialog_id}/conversations", json_body=payload,
                                            use_api_base=True, auth_kind="web")
        res_json = response.json()
        if response.status_code == 200 and res_json["code"] == 0:
            print(f"Success to drop chat session '{session_id}' from chat: {chat_name}")
        else:
            print(
                f"Fail to drop chat session '{session_id}' from chat {chat_name}, code: {res_json['code']}, message: {res_json['message']}")