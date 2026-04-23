async def cross_repo_search(query: str, file_or_path: Union[str, Path]) -> List[str]:
        """Search for a query across multiple repositories.

        This asynchronous function searches for the specified query in files
        located at the given path or file.

        Args:
            query (str): The search term to look for in the files.
            file_or_path (Union[str, Path]): The path to the file or directory
                where the search should be conducted. This can be a string path
                or a Path object.

        Returns:
            List[str]: A list of strings containing the paths of files that
            contain the query results.

        Raises:
            ValueError: If the query string is empty.
        """
        if not file_or_path or not Path(file_or_path).exists():
            raise ValueError(f'"{str(file_or_path)}" not exists')
        files = [file_or_path] if not Path(file_or_path).is_dir() else list_files(file_or_path)
        clusters, roots = IndexRepo.find_index_repo_path(files)
        futures = []
        others = set()
        for persist_path, filenames in clusters.items():
            if persist_path == OTHER_TYPE:
                others.update(filenames)
                continue
            root = roots[persist_path]
            repo = IndexRepo(persist_path=persist_path, root_path=root)
            futures.append(repo.search(query=query, filenames=list(filenames)))

        for i in others:
            futures.append(File.read_text_file(i))

        futures_results = []
        if futures:
            futures_results = await asyncio.gather(*futures)

        result = []
        v_result = []
        for i in futures_results:
            if not i:
                continue
            if isinstance(i, str):
                result.append(i)
            else:
                v_result.append(i)

        repo = IndexRepo()
        merged = await repo.merge(query=query, indices_list=v_result)
        return [i.text for i in merged] + result