async def confirm_comments(self, patch: PatchSet, comments: list[dict], points: list[Point]) -> list[dict]:
        points_dict = {point.id: point for point in points}
        new_comments = []
        for cmt in comments:
            try:
                point = points_dict[cmt.get("point_id")]

                code_start_line = cmt.get("code_start_line")
                code_end_line = cmt.get("code_end_line")
                # 如果代码位置为空的话，那么就将这条记录丢弃掉
                if not code_start_line or not code_end_line:
                    logger.info("False")
                    continue

                # 代码增加上下文，提升confirm的准确率
                code = get_code_block_from_patch(
                    patch, str(max(1, int(code_start_line) - 3)), str(int(code_end_line) + 3)
                )
                pattern = r"^[ \t\n\r(){}[\];,]*$"
                if re.match(pattern, code):
                    code = get_code_block_from_patch(
                        patch, str(max(1, int(code_start_line) - 5)), str(int(code_end_line) + 5)
                    )
                code_language = "Java"
                code_file_ext = cmt.get("commented_file", ".java").split(".")[-1]
                if code_file_ext == ".java":
                    code_language = "Java"
                elif code_file_ext == ".py":
                    code_language = "Python"
                prompt = CODE_REVIEW_COMFIRM_TEMPLATE.format(
                    code=code,
                    comment=cmt.get("comment"),
                    desc=point.text,
                    example=point.yes_example + "\n" + point.no_example,
                )
                system_prompt = [CODE_REVIEW_COMFIRM_SYSTEM_PROMPT.format(code_language=code_language)]
                resp = await self.llm.aask(prompt, system_msgs=system_prompt)
                if "True" in resp or "true" in resp:
                    new_comments.append(cmt)
            except Exception:
                logger.info("False")
        logger.info(f"original comments num: {len(comments)}, confirmed comments num: {len(new_comments)}")
        return new_comments