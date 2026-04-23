def encode(self, texts: list):
        batch_size = 512
        ress = []
        token_count = 0

        if self._is_contextualized():
            url = f"{self.base_url}/v1/contextualizedembeddings"
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                payload = {
                    "model": self.model_name,
                    "input": [[chunk] for chunk in batch],
                    "encoding_format": "base64_int8",
                }
                response = requests.post(url, headers=self.headers, json=payload)
                try:
                    res = response.json()
                    for doc in res["data"]:
                        for chunk_emb in doc["data"]:
                            ress.append(self._decode_base64_int8(chunk_emb["embedding"]))
                    token_count += res.get("usage", {}).get("total_tokens", 0)
                except Exception as _e:
                    log_exception(_e, response)
                    raise Exception(f"Error: {response.text}")
        else:
            url = f"{self.base_url}/v1/embeddings"
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                payload = {
                    "model": self.model_name,
                    "input": batch,
                    "encoding_format": "base64_int8",
                }
                response = requests.post(url, headers=self.headers, json=payload)
                try:
                    res = response.json()
                    for d in res["data"]:
                        ress.append(self._decode_base64_int8(d["embedding"]))
                    token_count += res.get("usage", {}).get("total_tokens", 0)
                except Exception as _e:
                    log_exception(_e, response)
                    raise Exception(f"Error: {response.text}")

        return np.array(ress), token_count