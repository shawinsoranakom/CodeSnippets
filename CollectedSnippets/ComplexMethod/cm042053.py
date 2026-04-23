async def get_codes(task_doc: Document, exclude: str, project_repo: ProjectRepo, use_inc: bool = False) -> str:
        """
        Get codes for generating the exclude file in various scenarios.

        Attributes:
            task_doc (Document): Document object of the task file.
            exclude (str): The file to be generated. Specifies the filename to be excluded from the code snippets.
            project_repo (ProjectRepo): ProjectRepo object of the project.
            use_inc (bool): Indicates whether the scenario involves incremental development. Defaults to False.

        Returns:
            str: Codes for generating the exclude file.
        """
        if not task_doc:
            return ""
        if not task_doc.content:
            task_doc = project_repo.docs.task.get(filename=task_doc.filename)
        m = json.loads(task_doc.content)
        code_filenames = m.get(TASK_LIST.key, []) if not use_inc else m.get(REFINED_TASK_LIST.key, [])
        codes = []
        src_file_repo = project_repo.srcs
        # Incremental development scenario
        if use_inc:
            for filename in src_file_repo.all_files:
                code_block_type = get_markdown_code_block_type(filename)
                # Exclude the current file from the all code snippets
                if filename == exclude:
                    # If the file is in the old workspace, use the old code
                    # Exclude unnecessary code to maintain a clean and focused main.py file, ensuring only relevant and
                    # essential functionality is included for the project’s requirements
                    if filename != "main.py":
                        # Use old code
                        doc = await src_file_repo.get(filename=filename)
                    # If the file is in the src workspace, skip it
                    else:
                        continue
                    codes.insert(
                        0, f"### The name of file to rewrite: `{filename}`\n```{code_block_type}\n{doc.content}```\n"
                    )
                    logger.info(f"Prepare to rewrite `{filename}`")
                # The code snippets are generated from the src workspace
                else:
                    doc = await src_file_repo.get(filename=filename)
                    # If the file does not exist in the src workspace, skip it
                    if not doc:
                        continue
                    codes.append(f"### File Name: `{filename}`\n```{code_block_type}\n{doc.content}```\n\n")

        # Normal scenario
        else:
            for filename in code_filenames:
                # Exclude the current file to get the code snippets for generating the current file
                if filename == exclude:
                    continue
                doc = await src_file_repo.get(filename=filename)
                if not doc:
                    continue
                code_block_type = get_markdown_code_block_type(filename)
                codes.append(f"### File Name: `{filename}`\n```{code_block_type}\n{doc.content}```\n\n")

        return "\n".join(codes)