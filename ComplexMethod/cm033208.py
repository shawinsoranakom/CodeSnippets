def list_chunks(self, command_dict):
        if self.server_type != "user":
            print("This command is only allowed in USER mode")
            return

        doc_id = command_dict["doc_id"]
        payload = {
            "doc_id": doc_id,
        }

        # Add optional parameters (only if explicitly provided)
        if "page" in command_dict:
            payload["page"] = command_dict["page"]
        if "size" in command_dict:
            payload["size"] = command_dict["size"]
        if "keywords" in command_dict and command_dict["keywords"]:
            payload["keywords"] = command_dict["keywords"]
        if "available_int" in command_dict:
            payload["available_int"] = command_dict["available_int"]

        response = self.http_client.request("POST", "/chunk/list", json_body=payload, use_api_base=False,
                                            auth_kind="web")
        res_json = response.json()
        if response.status_code == 200:
            if res_json["code"] == 0:
                chunks = res_json["data"]["chunks"]
                if chunks:
                    for i, chunk in enumerate(chunks):
                        print(f"\n--- Chunk {i+1} ---")
                        for key, value in chunk.items():
                            print(f"  {key}: {value}")
                else:
                    print("No chunks found")
            else:
                print(f"Fail to list chunks, code: {res_json['code']}, message: {res_json['message']}")
        else:
            print(f"Fail to list chunks, code: {res_json['code']}, message: {res_json['message']}")