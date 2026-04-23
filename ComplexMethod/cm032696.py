def encode(self, texts: list[str | bytes], task="retrieval.passage"):
        batch_size = 16
        ress = []
        token_count = 0
        input = []
        for text in texts:
            if isinstance(text, str):
                input.append({"text": text})
            elif isinstance(text, bytes):
                img_b64s = None
                try:
                    base64.b64decode(text, validate=True)
                    img_b64s = text.decode("utf8")
                except Exception:
                    img_b64s = base64.b64encode(text).decode("utf8")
                input.append({"image": img_b64s})  # base64 encoded image
        for i in range(0, len(texts), batch_size):
            data = {"model": self.model_name, "input": input[i : i + batch_size]}
            if "v4" in self.model_name:
                data["return_multivector"] = True

            if "v3" in self.model_name or "v4" in self.model_name:
                data["task"] = task
                data["truncate"] = True

            response = requests.post(self.base_url, headers=self.headers, json=data)
            try:
                res = response.json()
                for d in res["data"]:
                    if data.get("return_multivector", False):  # v4
                        token_embs = np.asarray(d["embeddings"], dtype=np.float32)
                        chunk_emb = token_embs.mean(axis=0)

                    else:
                        # v2/v3
                        chunk_emb = np.asarray(d["embedding"], dtype=np.float32)

                    ress.append(chunk_emb)

                token_count += total_token_count_from_response(res)
            except Exception as _e:
                log_exception(_e, response)
                raise Exception(f"Error: {response}")
        return np.array(ress), token_count