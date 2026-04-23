async def _add_batch(
        self,
        filenames: List[Union[str, Path]],
        delete_filenames: List[Union[str, Path]],
        file_datas: Dict[Union[str, Path], str],
    ):
        """Add and remove documents in a batch operation.

        Args:
            filenames (List[Union[str, Path]]): List of filenames to add.
            delete_filenames (List[Union[str, Path]]): List of filenames to delete.
        """
        if not filenames:
            return
        logger.info(f"update index repo, add {filenames}, remove {delete_filenames}")
        engine = None
        Context()
        if Path(self.persist_path).exists():
            logger.debug(f"load index from {self.persist_path}")
            engine = SimpleEngine.from_index(
                index_config=FAISSIndexConfig(persist_path=self.persist_path),
                retriever_configs=[FAISSRetrieverConfig()],
            )
            try:
                engine.delete_docs(filenames + delete_filenames)
                logger.info(f"delete docs {filenames + delete_filenames}")
                engine.add_docs(input_files=filenames)
                logger.info(f"add docs {filenames}")
            except NotImplementedError as e:
                logger.debug(f"{e}")
                filenames = list(set([str(i) for i in filenames] + list(self.fingerprints.keys())))
                engine = None
                logger.info(f"{e}. Rebuild all.")
        if not engine:
            engine = SimpleEngine.from_docs(
                input_files=[str(i) for i in filenames],
                retriever_configs=[FAISSRetrieverConfig()],
                ranker_configs=[LLMRankerConfig()],
            )
            logger.info(f"add docs {filenames}")
        engine.persist(persist_dir=self.persist_path)
        for i in filenames:
            content = file_datas.get(i) or await File.read_text_file(i)
            fp = generate_fingerprint(content)
            self.fingerprints[str(i)] = fp
        await awrite(filename=Path(self.persist_path) / self.fingerprint_filename, data=json.dumps(self.fingerprints))
        await self._save_meta()