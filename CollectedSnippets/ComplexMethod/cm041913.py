def set_mc_resume(self):
        self.qa_cache_questions_vectordb = ChromaVectorStore(
            collection_name="qa_cache_questions_vectordb",
            persist_dir=f"{MC_CKPT_DIR}/curriculum/vectordb",
        )

        self.vectordb = ChromaVectorStore(
            collection_name="skill_vectordb",
            persist_dir=f"{MC_CKPT_DIR}/skill/vectordb",
        )

        if Config.default().resume:
            logger.info(f"Loading Action Developer from {MC_CKPT_DIR}/action")
            self.chest_memory = read_json_file(f"{MC_CKPT_DIR}/action/chest_memory.json")

            logger.info(f"Loading Curriculum Agent from {MC_CKPT_DIR}/curriculum")
            self.completed_tasks = read_json_file(f"{MC_CKPT_DIR}/curriculum/completed_tasks.json")
            self.failed_tasks = read_json_file(f"{MC_CKPT_DIR}/curriculum/failed_tasks.json")

            logger.info(f"Loading Skill Manager from {MC_CKPT_DIR}/skill\033[0m")
            self.skills = read_json_file(f"{MC_CKPT_DIR}/skill/skills.json")

            logger.info(f"Loading Qa Cache from {MC_CKPT_DIR}/curriculum\033[0m")
            self.qa_cache = read_json_file(f"{MC_CKPT_DIR}/curriculum/qa_cache.json")

            if self.vectordb._collection.count() == 0:
                logger.info(self.vectordb._collection.count())
                # Set vdvs for skills & qa_cache
                skill_desps = [skill["description"] for program_name, skill in self.skills.items()]
                program_names = [program_name for program_name, skill in self.skills.items()]
                metadatas = [{"name": program_name} for program_name in program_names]
                # add vectordb from file
                self.vectordb.add_texts(
                    texts=skill_desps,
                    ids=program_names,
                    metadatas=metadatas,
                )
                self.vectordb.persist()

            logger.info(self.qa_cache_questions_vectordb._collection.count())
            if self.qa_cache_questions_vectordb._collection.count() == 0:
                questions = [question for question, answer in self.qa_cache.items()]

                self.qa_cache_questions_vectordb.add_texts(texts=questions)

                self.qa_cache_questions_vectordb.persist()

                logger.info(
                    f"INIT_CHECK: There are {self.vectordb._collection.count()} skills in vectordb and {len(self.skills)} skills in skills.json."
                )
                # Check if Skill Manager's vectordb right using
                assert self.vectordb._collection.count() == len(self.skills), (
                    f"Skill Manager's vectordb is not synced with skills.json.\n"
                    f"There are {self.vectordb._collection.count()} skills in vectordb but {len(self.skills)} skills in skills.json.\n"
                    f"Did you set resume=False when initializing the manager?\n"
                    f"You may need to manually delete the vectordb directory for running from scratch."
                )

                logger.info(
                    f"INIT_CHECK: There are {self.qa_cache_questions_vectordb._collection.count()} qa_cache in vectordb and {len(self.qa_cache)} questions in qa_cache.json."
                )
                assert self.qa_cache_questions_vectordb._collection.count() == len(self.qa_cache), (
                    f"Curriculum Agent's qa cache question vectordb is not synced with qa_cache.json.\n"
                    f"There are {self.qa_cache_questions_vectordb._collection.count()} questions in vectordb "
                    f"but {len(self.qa_cache)} questions in qa_cache.json.\n"
                    f"Did you set resume=False when initializing the agent?\n"
                    f"You may need to manually delete the qa cache question vectordb directory for running from scratch.\n"
                )