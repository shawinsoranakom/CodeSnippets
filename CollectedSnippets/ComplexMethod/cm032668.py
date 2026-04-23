def miracl_index(self, file_path, corpus_path, index_name):
        corpus_total = {}
        for corpus_file in os.listdir(corpus_path):
            tmp_data = pd.read_json(os.path.join(corpus_path, corpus_file), lines=True)
            for index, i in tmp_data.iterrows():
                corpus_total[i['docid']] = i['text']

        topics_total = {}
        for topics_file in os.listdir(os.path.join(file_path, 'topics')):
            if 'test' in topics_file:
                continue
            tmp_data = pd.read_csv(os.path.join(file_path, 'topics', topics_file), sep='\t', names=['qid', 'query'])
            for index, i in tmp_data.iterrows():
                topics_total[i['qid']] = i['query']

        qrels = defaultdict(dict)
        texts = defaultdict(dict)
        docs_count = 0
        docs = []
        for qrels_file in os.listdir(os.path.join(file_path, 'qrels')):
            if 'test' in qrels_file:
                continue
            if docs_count >= max_docs:
                break

            tmp_data = pd.read_csv(os.path.join(file_path, 'qrels', qrels_file), sep='\t',
                                   names=['qid', 'Q0', 'docid', 'relevance'])
            for i in tqdm(range(len(tmp_data)), colour="green", desc="Indexing:" + qrels_file):
                if docs_count >= max_docs:
                    break
                query = topics_total[tmp_data.iloc[i]['qid']]
                text = corpus_total[tmp_data.iloc[i]['docid']]
                rel = tmp_data.iloc[i]['relevance']
                d = {
                    "id": get_uuid(),
                    "kb_id": self.kb.id,
                    "docnm_kwd": "xxxxx",
                    "doc_id": "ksksks"
                }
                tokenize(d, text, 'english')
                docs.append(d)
                texts[d["id"]] = text
                qrels[query][d["id"]] = int(rel)
                if len(docs) >= 32:
                    docs_count += len(docs)
                    docs, vector_size = self.embedding(docs)
                    self.init_index(vector_size)
                    settings.docStoreConn.insert(docs, self.index_name)
                    docs = []

        docs, vector_size = self.embedding(docs)
        self.init_index(vector_size)
        settings.docStoreConn.insert(docs, self.index_name)
        return qrels, texts