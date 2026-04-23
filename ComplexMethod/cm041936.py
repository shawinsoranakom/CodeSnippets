async def run(self, patch: PatchSet, comments: list[dict], output_dir: Optional[str] = None) -> str:
        patch: PatchSet = rm_patch_useless_part(patch)
        patch: PatchSet = add_line_num_on_patch(patch)

        #
        for comment in comments:
            code_start_line = comment.get("code_start_line")
            code_end_line = comment.get("code_end_line")
            # 如果代码位置为空的话，那么就将这条记录丢弃掉
            if code_start_line and code_end_line:
                code = get_code_block_from_patch(
                    patch, str(max(1, int(code_start_line) - 3)), str(int(code_end_line) + 3)
                )
                pattern = r"^[ \t\n\r(){}[\];,]*$"
                if re.match(pattern, code):
                    code = get_code_block_from_patch(
                        patch, str(max(1, int(code_start_line) - 5)), str(int(code_end_line) + 5)
                    )
                # 代码增加上下文，提升代码修复的准确率
                comment["code"] = code
            # 去掉CR时LLM给的comment的影响，应该使用既定的修复方案
            comment.pop("comment")

        # 按照 commented_file 字段进行分组
        comments.sort(key=lambda x: x["commented_file"])
        grouped_comments = {
            key: list(group) for key, group in itertools.groupby(comments, key=lambda x: x["commented_file"])
        }
        resp = None
        for patched_file in patch:
            patch_target_file_name = str(patched_file.path).split("/")[-1]
            if patched_file.path not in grouped_comments:
                continue
            comments_prompt = ""
            index = 1
            for grouped_comment in grouped_comments[patched_file.path]:
                comments_prompt += f"""
                    <comment{index}>
                    {grouped_comment}
                    </comment{index}>\n
                """
                index += 1
            prompt = MODIFY_CODE_PROMPT.format(patch=patched_file, comments=comments_prompt)
            output_dir = (
                Path(output_dir)
                if output_dir
                else self.config.workspace.path / "modify_code" / str(datetime.date.today()) / self.pr
            )
            patch_file = output_dir / f"{patch_target_file_name}.patch"
            patch_file.parent.mkdir(exist_ok=True, parents=True)
            async with EditorReporter(enable_llm_stream=True) as reporter:
                await reporter.async_report(
                    {"type": "Patch", "src_path": str(patch_file), "filename": patch_file.name}, "meta"
                )
                resp = await self.llm.aask(msg=prompt, system_msgs=[SYSTEM_MSGS_PROMPT])
                resp = CodeParser.parse_code(resp, "diff")
                with open(patch_file, "w", encoding="utf-8") as file:
                    file.writelines(resp)
                await reporter.async_report(patch_file)
        return resp