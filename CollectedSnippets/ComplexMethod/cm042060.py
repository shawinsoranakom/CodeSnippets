async def _guess_src_workspace(self) -> Path:
        files = list_files(self.context.repo.workdir)
        dirs = [i.parent for i in files if i.name == "__init__.py"]
        distinct = set()
        for i in dirs:
            done = False
            for j in distinct:
                if i.is_relative_to(j):
                    done = True
                    break
                if j.is_relative_to(i):
                    break
            if not done:
                distinct = {j for j in distinct if not j.is_relative_to(i)}
                distinct.add(i)
        if len(distinct) == 1:
            return list(distinct)[0]
        prompt = "\n".join([f"- {str(i)}" for i in distinct])
        rsp = await self.llm.aask(
            prompt,
            system_msgs=[
                "You are a tool to choose the source code path from a list of paths based on the directory name.",
                "You should identify the source code path among paths such as unit test path, examples path, etc.",
                "Return a markdown JSON object containing:\n"
                '- a "src" field containing the source code path;\n'
                '- a "reason" field containing explaining why other paths is not the source code path\n',
            ],
        )
        logger.debug(rsp)
        json_blocks = parse_json_code_block(rsp)

        class Data(BaseModel):
            src: str
            reason: str

        data = Data.model_validate_json(json_blocks[0])
        logger.info(f"src_workspace: {data.src}")
        return Path(data.src)