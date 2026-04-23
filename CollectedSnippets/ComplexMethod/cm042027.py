async def update_graph_db_with_file_info(graph_db: "GraphRepository", file_info: RepoFileInfo):
        """Insert information of RepoFileInfo into the specified graph repository.

        This function updates the provided graph repository with information from the given RepoFileInfo object.
        The function inserts triples related to various dimensions such as file type, class, class method, function,
        global variable, and page info.

        Triple Patterns:
        - (?, is, [file type])
        - (?, has class, ?)
        - (?, is, [class])
        - (?, has class method, ?)
        - (?, has function, ?)
        - (?, is, [function])
        - (?, is, global variable)
        - (?, has page info, ?)

        Args:
            graph_db (GraphRepository): The graph repository object to be updated.
            file_info (RepoFileInfo): The RepoFileInfo object containing information to be inserted.

        Example:
            await update_graph_db_with_file_info(my_graph_repo, my_file_info)
            # Updates 'my_graph_repo' with information from 'my_file_info'.
        """
        await graph_db.insert(subject=file_info.file, predicate=GraphKeyword.IS, object_=GraphKeyword.SOURCE_CODE)
        file_types = {".py": "python", ".js": "javascript"}
        file_type = file_types.get(Path(file_info.file).suffix, GraphKeyword.NULL)
        await graph_db.insert(subject=file_info.file, predicate=GraphKeyword.IS, object_=file_type)
        for c in file_info.classes:
            class_name = c.get("name", "")
            # file -> class
            await graph_db.insert(
                subject=file_info.file,
                predicate=GraphKeyword.HAS_CLASS,
                object_=concat_namespace(file_info.file, class_name),
            )
            # class detail
            await graph_db.insert(
                subject=concat_namespace(file_info.file, class_name),
                predicate=GraphKeyword.IS,
                object_=GraphKeyword.CLASS,
            )
            methods = c.get("methods", [])
            for fn in methods:
                await graph_db.insert(
                    subject=concat_namespace(file_info.file, class_name),
                    predicate=GraphKeyword.HAS_CLASS_METHOD,
                    object_=concat_namespace(file_info.file, class_name, fn),
                )
                await graph_db.insert(
                    subject=concat_namespace(file_info.file, class_name, fn),
                    predicate=GraphKeyword.IS,
                    object_=GraphKeyword.CLASS_METHOD,
                )
        for f in file_info.functions:
            # file -> function
            await graph_db.insert(
                subject=file_info.file, predicate=GraphKeyword.HAS_FUNCTION, object_=concat_namespace(file_info.file, f)
            )
            # function detail
            await graph_db.insert(
                subject=concat_namespace(file_info.file, f), predicate=GraphKeyword.IS, object_=GraphKeyword.FUNCTION
            )
        for g in file_info.globals:
            await graph_db.insert(
                subject=concat_namespace(file_info.file, g),
                predicate=GraphKeyword.IS,
                object_=GraphKeyword.GLOBAL_VARIABLE,
            )
        for code_block in file_info.page_info:
            if code_block.tokens:
                await graph_db.insert(
                    subject=concat_namespace(file_info.file, *code_block.tokens),
                    predicate=GraphKeyword.HAS_PAGE_INFO,
                    object_=code_block.model_dump_json(),
                )
            for k, v in code_block.properties.items():
                await graph_db.insert(
                    subject=concat_namespace(file_info.file, k, v),
                    predicate=GraphKeyword.HAS_PAGE_INFO,
                    object_=code_block.model_dump_json(),
                )