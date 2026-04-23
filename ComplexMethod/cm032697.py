def encode(self, texts: list):
        batch_size = 16
        ress = []
        token_count = 0
        for i in range(0, len(texts), batch_size):
            texts_batch = texts[i : i + batch_size]
            if self.model_name in ["BAAI/bge-large-zh-v1.5", "BAAI/bge-large-en-v1.5"]:
                # limit 512, 340 is almost safe
                texts_batch = [" " if not text.strip() else truncate(text, 256) for text in texts_batch]
            else:
                texts_batch = [" " if not text.strip() else text for text in texts_batch]

            payload = {
                "model": self.model_name,
                "input": texts_batch,
                "encoding_format": "float",
            }
            response = requests.post(self.base_url, json=payload, headers=self.headers)
            try:
                res = response.json()
                ress.extend([d["embedding"] for d in res["data"]])
                token_count += total_token_count_from_response(res)
            except Exception as _e:
                log_exception(_e, response)
                raise Exception(f"Error: {response}")

        return np.array(ress), token_count