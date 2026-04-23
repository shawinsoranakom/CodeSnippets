def set_metadata(self, command_dict):
        if self.server_type != "user":
            print("This command is only allowed in USER mode")
            return

        doc_id = command_dict["doc_id"]
        meta_json_str = command_dict["meta"]

        # Parse JSON string to dict
        import json
        try:
            meta_fields = json.loads(meta_json_str)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON format: {e}")
            return

        # Step 1: Get document info to find kb_id (dataset_id)
        doc_error_msg, docs = self._get_documents_by_ids([doc_id])
        if doc_error_msg:
            print(doc_error_msg)
            return

        if len(docs) == 0:
            print(f"no document found for {doc_id}")
            return

        dataset_id = docs[0].get("dataset_id")
        if not dataset_id:
            print(f"Dataset ID not found for document: {doc_id}")
            return

        # Send meta as JSON string
        payload = {
            "meta_fields": meta_fields,
        }

        response = self.http_client.request(
            "PATCH",
            f"/datasets/{dataset_id}/documents/{doc_id}",
            json_body=payload,
            use_api_base=True,
            auth_kind="web"
        )

        res_json = response.json()
        if response.status_code == 200:
            if res_json.get("code") == 0:
                print(f"Success to set metadata for document: {doc_id}")
            else:
                print(f"Fail to set metadata, code: {res_json.get('code')}, message: {res_json.get('message')}")
        else:
            print(f"Fail to set metadata, HTTP {response.status_code}: {res_json.get('message', 'no message')}")