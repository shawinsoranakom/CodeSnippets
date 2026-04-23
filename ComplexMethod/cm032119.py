def init_knowledge_vector_store(self,
                                    filepath,
                                    vs_path: str or os.PathLike = None,
                                    sentence_size=SENTENCE_SIZE,
                                    text2vec=None):
        loaded_files = []
        failed_files = []
        if isinstance(filepath, str):
            if not os.path.exists(filepath):
                logger.error("路径不存在")
                return None
            elif os.path.isfile(filepath):
                file = os.path.split(filepath)[-1]
                try:
                    docs = load_file(filepath, SENTENCE_SIZE)
                    logger.info(f"{file} 已成功加载")
                    loaded_files.append(filepath)
                except Exception as e:
                    logger.error(e)
                    logger.error(f"{file} 未能成功加载")
                    return None
            elif os.path.isdir(filepath):
                docs = []
                for file in tqdm(os.listdir(filepath), desc="加载文件"):
                    fullfilepath = os.path.join(filepath, file)
                    try:
                        docs += load_file(fullfilepath, SENTENCE_SIZE)
                        loaded_files.append(fullfilepath)
                    except Exception as e:
                        logger.error(e)
                        failed_files.append(file)

                if len(failed_files) > 0:
                    logger.error("以下文件未能成功加载：")
                    for file in failed_files:
                        logger.error(f"{file}\n")

        else:
            docs = []
            for file in filepath:
                docs += load_file(file, SENTENCE_SIZE)
                logger.info(f"{file} 已成功加载")
                loaded_files.append(file)

        if len(docs) > 0:
            logger.info("文件加载完毕，正在生成向量库")
            if vs_path and os.path.isdir(vs_path):
                try:
                    self.vector_store = FAISS.load_local(vs_path, text2vec)
                    self.vector_store.add_documents(docs)
                except:
                    self.vector_store = FAISS.from_documents(docs, text2vec)
            else:
                self.vector_store = FAISS.from_documents(docs, text2vec)  # docs 为Document列表

            self.vector_store.save_local(vs_path)
            return vs_path, loaded_files
        else:
            raise RuntimeError("文件加载失败，请检查文件格式是否正确")