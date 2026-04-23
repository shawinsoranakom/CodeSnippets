def parse_dataset_docs(self, command_dict):
        if self.server_type != "user":
            print("This command is only allowed in USER mode")

        dataset_name = command_dict["dataset_name"]
        dataset_id = self._get_dataset_id(dataset_name)
        if dataset_id is None:
            return

        res_json = self._list_documents(dataset_name, dataset_id)
        if res_json is None:
            return

        document_names = command_dict["document_names"]
        document_ids = []
        to_parse_doc_names = []
        for doc in res_json:
            doc_name = doc["name"]
            if doc_name in document_names:
                document_ids.append(doc["id"])
                document_names.remove(doc_name)
                to_parse_doc_names.append(doc_name)

        if len(document_ids) == 0:
            print(f"No documents found in {dataset_name}")
            return

        if len(document_names) != 0:
            print(f"Documents {document_names} not found in {dataset_name}")

        payload = {"doc_ids": document_ids, "run": 1}
        response = self.http_client.request("POST", "/document/run", json_body=payload, use_api_base=False,
                                            auth_kind="web")
        res_json = response.json()
        if response.status_code == 200 and res_json["code"] == 0:
            print(f"Success to parse {to_parse_doc_names} of {dataset_name}")
        else:
            print(
                f"Fail to parse documents {res_json["data"]["docs"]}, code: {res_json['code']}, message: {res_json['message']}")