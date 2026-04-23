def parse_dataset(self, command_dict):
        if self.server_type != "user":
            print("This command is only allowed in USER mode")

        dataset_name = command_dict["dataset_name"]
        dataset_id = self._get_dataset_id(dataset_name)
        if dataset_id is None:
            return

        res_json = self._list_documents(dataset_name, dataset_id)
        if res_json is None:
            return
        document_ids = []
        for doc in res_json:
            document_ids.append(doc["id"])

        payload = {"doc_ids": document_ids, "run": 1}
        response = self.http_client.request("POST", "/document/run", json_body=payload, use_api_base=False,
                                            auth_kind="web")
        res_json = response.json()
        if response.status_code == 200 and res_json["code"] == 0:
            pass
        else:
            print(f"Fail to parse dataset {dataset_name}, code: {res_json['code']}, message: {res_json['message']}")

        if command_dict["method"] == "async":
            print(f"Success to start parse dataset {dataset_name}")
            return
        else:
            print(f"Start to parse dataset {dataset_name}, please wait...")
            if self._wait_parse_done(dataset_name, dataset_id):
                print(f"Success to parse dataset {dataset_name}")
            else:
                print(f"Parse dataset {dataset_name} timeout")