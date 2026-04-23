def ms_marco_index(self, file_path, index_name):
        qrels = defaultdict(dict)
        texts = defaultdict(dict)
        docs_count = 0
        docs = []
        filelist = sorted(os.listdir(file_path))

        for fn in filelist:
            if docs_count >= max_docs:
                break
            if not fn.endswith(".parquet"):
                continue
            data = pd.read_parquet(os.path.join(file_path, fn))
            for i in tqdm(range(len(data)), colour="green", desc="Tokenizing:" + fn):
                if docs_count >= max_docs:
                    break
                query = data.iloc[i]['query']
                for rel, text in zip(data.iloc[i]['passages']['is_selected'], data.iloc[i]['passages']['passage_text']):
                    d = {
                        "id": get_uuid(),
                        "kb_id": self.kb.id,
                        "docnm_kwd": "xxxxx",
                        "doc_id": "ksksks"
                    }
                    tokenize(d, text, "english")
                    docs.append(d)
                    texts[d["id"]] = text
                    qrels[query][d["id"]] = int(rel)
                if len(docs) >= 32:
                    docs_count += len(docs)
                    docs, vector_size = self.embedding(docs)
                    self.init_index(vector_size)
                    settings.docStoreConn.insert(docs, self.index_name, self.kb_id)
                    docs = []

        if docs:
            docs, vector_size = self.embedding(docs)
            self.init_index(vector_size)
            settings.docStoreConn.insert(docs, self.index_name, self.kb_id)
        return qrels, texts