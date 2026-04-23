async def search(
        self, query: str, filenames: Optional[List[Path]] = None
    ) -> Optional[List[Union[NodeWithScore, TextScore]]]:
        """Search for documents related to the given query.

        Args:
            query (str): The search query.
            filenames (Optional[List[Path]]): A list of filenames to filter the search.

        Returns:
            Optional[List[Union[NodeWithScore, TextScore]]]: A list of search results containing NodeWithScore or TextScore.
        """
        encoding = tiktoken.get_encoding("cl100k_base")
        result: List[Union[NodeWithScore, TextScore]] = []
        filenames, excludes = await self._filter(filenames)
        if not filenames:
            raise ValueError(f"Unsupported file types: {[str(i) for i in excludes]}")
        resource = EditorReporter()
        for i in filenames:
            await resource.async_report(str(i), "path")
        filter_filenames = set()
        meta = await self._read_meta()
        new_files = {}
        for i in filenames:
            if Path(i).suffix.lower() in {".pdf", ".doc", ".docx"}:
                if str(i) not in self.fingerprints:
                    new_files[i] = ""
                    logger.warning(f'file: "{i}" not indexed')
                filter_filenames.add(str(i))
                continue
            content = await File.read_text_file(i)
            token_count = len(encoding.encode(content))
            if not self._is_buildable(
                token_count, min_token_count=meta.min_token_count, max_token_count=meta.max_token_count
            ):
                result.append(TextScore(filename=str(i), text=content))
                continue
            file_fingerprint = generate_fingerprint(content)
            if str(i) not in self.fingerprints or (self.fingerprints.get(str(i)) != file_fingerprint):
                new_files[i] = content
                logger.warning(f'file: "{i}" changed but not indexed')
                continue
            filter_filenames.add(str(i))
        if new_files:
            added, others = await self.add(paths=list(new_files.keys()), file_datas=new_files)
            filter_filenames.update([str(i) for i in added])
            for i in others:
                result.append(TextScore(filename=str(i), text=new_files.get(i)))
                filter_filenames.discard(str(i))
        nodes = await self._search(query=query, filters=filter_filenames)
        return result + nodes