def generate(self) -> str:
        content = f"# {self.title}\n\n"
        url = "https://github.com/vllm-project/vllm/"
        url += "tree/main" if self.path.is_dir() else "blob/main"
        content += f"Source <{url}/{self.path.relative_to(ROOT_DIR)}>.\n\n"

        # Use long code fence to avoid issues with
        # included files containing code fences too
        code_fence = "``````"

        if self.main_file is not None:
            # Single file example or multi file example with a README
            if self.is_code:
                content += (
                    f"{code_fence}{self.main_file.suffix[1:]}\n"
                    f'--8<-- "{self.main_file}"\n'
                    f"{code_fence}\n"
                )
            else:
                with open(self.main_file, encoding="utf-8") as f:
                    # Skip the title from md snippets as it's been included above
                    main_content = f.readlines()[1:]
                content += self.fix_relative_links("".join(main_content))
            content += "\n"
        else:
            # Multi file example without a README
            for file in self.other_files:
                file_title = title(str(file.relative_to(self.path).with_suffix("")))
                content += f"## {file_title}\n\n"
                content += (
                    f'{code_fence}{file.suffix[1:]}\n--8<-- "{file}"\n{code_fence}\n\n'
                )
            return content

        if not self.other_files:
            return content

        content += "## Example materials\n\n"
        for file in self.other_files:
            content += f'??? abstract "{file.relative_to(self.path)}"\n'
            if file.suffix != ".md":
                content += f"    {code_fence}{file.suffix[1:]}\n"
            content += f'    --8<-- "{file}"\n'
            if file.suffix != ".md":
                content += f"    {code_fence}\n"

        return content