def update_chunk(self, command_dict):
        if self.server_type != "user":
            print("This command is only allowed in USER mode")
            return

        chunk_id = command_dict["chunk_id"]
        dataset_name = command_dict["dataset_name"]
        json_body_str = command_dict["json_body"]

        # Get dataset_id from dataset_name
        dataset_id = self._get_dataset_id(dataset_name)
        if dataset_id is None:
            return

        # Get doc_id from chunk_id via GET /chunk/get
        response = self.http_client.request("GET", f"/chunk/get?chunk_id={chunk_id}", use_api_base=False,
                                            auth_kind="web")
        res_json = response.json()
        if response.status_code != 200:
            print(f"Fail to get chunk info, code: {res_json.get('code')}, message: {res_json.get('message')}")
            return

        doc_id = None
        if res_json.get("code") == 0 and res_json.get("data"):
            doc_id = res_json["data"].get("doc_id")

        if not doc_id:
            print(f"Could not find document_id for chunk {chunk_id}")
            return

        # Parse json_body
        try:
            payload = json.loads(json_body_str)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON body: {e}")
            return

        # Add IDs to payload
        payload["dataset_id"] = dataset_id
        payload["document_id"] = doc_id
        payload["chunk_id"] = chunk_id

        # Call POST /v1/chunk/update
        response = self.http_client.request("POST", "/chunk/update", json_body=payload, use_api_base=False, auth_kind="web")
        res_json = response.json()
        if response.status_code == 200:
            if res_json.get("code") == 0:
                print(f"Success to update chunk: {chunk_id}")
            else:
                print(f"Fail to update chunk, code: {res_json.get('code')}, message: {res_json.get('message')}")
        else:
            print(f"Fail to update chunk, HTTP {response.status_code}")