def chat_on_session(self, command):
        if self.server_type != "user":
            print("This command is only allowed in USER mode")
        message = command["message"]
        session_id = command["session_id"]

        # Prepare payload for completion API
        # Note: stream parameter is not sent, server defaults to stream=True
        payload = {
            "conversation_id": session_id,
            "messages": [{"role": "user", "content": message}]
        }

        response = self.http_client.request("POST", "/conversation/completion", json_body=payload,
                                            use_api_base=False, auth_kind="web", stream=True)

        if response.status_code != 200:
            print(f"Fail to chat on session, status code: {response.status_code}")
            return

        print("Assistant: ", end="", flush=True)
        full_answer = ""
        for line in response.iter_lines():
            if not line:
                continue
            line_str = line.decode('utf-8')
            if not line_str.startswith('data:'):
                continue
            data_str = line_str[5:].strip()
            if data_str == '[DONE]':
                break
            try:
                data_json = json.loads(data_str)
                if data_json.get("code") != 0:
                    print(
                        f"\nFail to chat on session, code: {data_json.get('code')}, message: {data_json.get('message', '')}")
                    return
                # Check if it's the final message
                if data_json.get("data") is True:
                    break
                answer = data_json.get("data", {}).get("answer", "")
                if answer:
                    print(answer, end="", flush=True)
                    full_answer += answer
            except json.JSONDecodeError:
                continue
        print()