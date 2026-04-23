def list_user_documents_metadata_summary(self, command_dict):
        if self.server_type != "user":
            print("This command is only allowed in USER mode")
            return

        dataset_name = command_dict["dataset_name"]
        doc_ids = command_dict.get("document_ids", [])

        kb_id = self._get_dataset_id(dataset_name)
        if kb_id is None:
            return

        payload = {"kb_id": kb_id}
        if doc_ids:
            payload["doc_ids"] = doc_ids
        response = self.http_client.request("POST", "/document/metadata/summary", json_body=payload,
                                            use_api_base=False, auth_kind="web")
        res_json = response.json()
        if response.status_code == 200:
            summary = res_json.get("data", {}).get("summary", {})
            if not summary:
                if doc_ids:
                    print(f"No metadata summary found for documents: {', '.join(doc_ids)}")
                else:
                    print(f"No metadata summary found in dataset {dataset_name}")
                return
            if doc_ids:
                print(f"Metadata summary for document(s): {', '.join(doc_ids)}")
            else:
                print(f"Metadata summary for all documents in dataset: {dataset_name}")
            print("-" * 60)
            for field_name, field_info in summary.items():
                field_type = field_info.get("type", "unknown")
                values = field_info.get("values", [])
                print(f"\nField: {field_name} (type: {field_type})")
                print(f"  Total unique values: {len(values)}")
                if values:
                    print("  Values:")
                    for value, count in values:
                        print(f"    {value}: {count}")
        else:
            print(f"Fail to get metadata summary, code: {res_json.get('code')}, message: {res_json.get('message')}")