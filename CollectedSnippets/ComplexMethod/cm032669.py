def __call__(self, dataset, file_path, miracl_corpus=''):
        if dataset == "ms_marco_v1.1":
            self.tenant_id = "benchmark_ms_marco_v11"
            self.index_name = search.index_name(self.tenant_id)
            qrels, texts = self.ms_marco_index(file_path, "benchmark_ms_marco_v1.1")
            run = self._get_retrieval(qrels)
            print(dataset, evaluate(Qrels(qrels), Run(run), ["ndcg@10", "map@5", "mrr@10"]))
            self.save_results(qrels, run, texts, dataset, file_path)
        if dataset == "trivia_qa":
            self.tenant_id = "benchmark_trivia_qa"
            self.index_name = search.index_name(self.tenant_id)
            qrels, texts = self.trivia_qa_index(file_path, "benchmark_trivia_qa")
            run = self._get_retrieval(qrels)
            print(dataset, evaluate(Qrels(qrels), Run(run), ["ndcg@10", "map@5", "mrr@10"]))
            self.save_results(qrels, run, texts, dataset, file_path)
        if dataset == "miracl":
            for lang in ['ar', 'bn', 'de', 'en', 'es', 'fa', 'fi', 'fr', 'hi', 'id', 'ja', 'ko', 'ru', 'sw', 'te', 'th',
                         'yo', 'zh']:
                if not os.path.isdir(os.path.join(file_path, 'miracl-v1.0-' + lang)):
                    print('Directory: ' + os.path.join(file_path, 'miracl-v1.0-' + lang) + ' not found!')
                    continue
                if not os.path.isdir(os.path.join(file_path, 'miracl-v1.0-' + lang, 'qrels')):
                    print('Directory: ' + os.path.join(file_path, 'miracl-v1.0-' + lang, 'qrels') + 'not found!')
                    continue
                if not os.path.isdir(os.path.join(file_path, 'miracl-v1.0-' + lang, 'topics')):
                    print('Directory: ' + os.path.join(file_path, 'miracl-v1.0-' + lang, 'topics') + 'not found!')
                    continue
                if not os.path.isdir(os.path.join(miracl_corpus, 'miracl-corpus-v1.0-' + lang)):
                    print('Directory: ' + os.path.join(miracl_corpus, 'miracl-corpus-v1.0-' + lang) + ' not found!')
                    continue
                self.tenant_id = "benchmark_miracl_" + lang
                self.index_name = search.index_name(self.tenant_id)
                self.initialized_index = False
                qrels, texts = self.miracl_index(os.path.join(file_path, 'miracl-v1.0-' + lang),
                                                 os.path.join(miracl_corpus, 'miracl-corpus-v1.0-' + lang),
                                                 "benchmark_miracl_" + lang)
                run = self._get_retrieval(qrels)
                print(dataset, evaluate(Qrels(qrels), Run(run), ["ndcg@10", "map@5", "mrr@10"]))
                self.save_results(qrels, run, texts, dataset, file_path)