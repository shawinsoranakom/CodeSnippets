async def _get_document_metadata_cache(self, dataset_ids, *, api_key: str, force_refresh=False):
        """Cache document metadata for all documents in the specified datasets"""
        document_cache = {}
        dataset_cache = {}

        try:
            for dataset_id in dataset_ids:
                dataset_meta = None if force_refresh else self._get_cached_dataset_metadata(dataset_id)
                if not dataset_meta:
                    # First get dataset info for name
                    dataset_res = await self._get("/datasets", {"id": dataset_id, "page_size": 1}, api_key=api_key)
                    if dataset_res and dataset_res.status_code == 200:
                        dataset_data = dataset_res.json()
                        if dataset_data.get("code") == 0 and dataset_data.get("data"):
                            dataset_info = dataset_data["data"][0]
                            dataset_meta = {"name": dataset_info.get("name", "Unknown"), "description": dataset_info.get("description", "")}
                            self._set_cached_dataset_metadata(dataset_id, dataset_meta)
                if dataset_meta:
                    dataset_cache[dataset_id] = dataset_meta

                docs = None if force_refresh else self._get_cached_document_metadata_by_dataset(dataset_id)
                if docs is None:
                    page = 1
                    page_size = 30
                    doc_id_meta_list = []
                    docs = {}
                    while page:
                        docs_res = await self._get(f"/datasets/{dataset_id}/documents?page={page}", api_key=api_key)
                        if not docs_res:
                            break
                        docs_data = docs_res.json()
                        if docs_data.get("code") == 0 and docs_data.get("data", {}).get("docs"):
                            for doc in docs_data["data"]["docs"]:
                                doc_id = doc.get("id")
                                if not doc_id:
                                    continue
                                doc_meta = {
                                    "document_id": doc_id,
                                    "name": doc.get("name", ""),
                                    "location": doc.get("location", ""),
                                    "type": doc.get("type", ""),
                                    "size": doc.get("size"),
                                    "chunk_count": doc.get("chunk_count"),
                                    "create_date": doc.get("create_date", ""),
                                    "update_date": doc.get("update_date", ""),
                                    "token_count": doc.get("token_count"),
                                    "thumbnail": doc.get("thumbnail", ""),
                                    "dataset_id": doc.get("dataset_id", dataset_id),
                                    "meta_fields": doc.get("meta_fields", {}),
                                }
                                doc_id_meta_list.append((doc_id, doc_meta))
                                docs[doc_id] = doc_meta

                            page += 1
                            if docs_data.get("data", {}).get("total", 0) - page * page_size <= 0:
                                page = None

                        self._set_cached_document_metadata_by_dataset(dataset_id, doc_id_meta_list)
                if docs:
                    document_cache.update(docs)

        except Exception as e:
            # Gracefully handle metadata cache failures
            logging.error(f"Problem building the document metadata cache: {str(e)}")
            pass

        return document_cache, dataset_cache