async def run(self, *args, **kwargs) -> CodingContext:
        iterative_code = self.i_context.code_doc.content
        k = self.context.config.code_validate_k_times or 1

        for i in range(k):
            format_example = FORMAT_EXAMPLE.format(filename=self.i_context.code_doc.filename)
            task_content = self.i_context.task_doc.content if self.i_context.task_doc else ""
            code_context = await WriteCode.get_codes(
                self.i_context.task_doc,
                exclude=self.i_context.filename,
                project_repo=self.repo,
                use_inc=self.config.inc,
            )

            ctx_list = [
                "## System Design\n" + str(self.i_context.design_doc) + "\n",
                "## Task\n" + task_content + "\n",
                "## Code Files\n" + code_context + "\n",
            ]
            if self.config.inc:
                requirement_doc = await Document.load(filename=self.input_args.requirements_filename)
                insert_ctx_list = [
                    "## User New Requirements\n" + str(requirement_doc) + "\n",
                    "## Code Plan And Change\n" + str(self.i_context.code_plan_and_change_doc) + "\n",
                ]
                ctx_list = insert_ctx_list + ctx_list

            context_prompt = PROMPT_TEMPLATE.format(
                context="\n".join(ctx_list),
                code=iterative_code,
                filename=self.i_context.code_doc.filename,
            )
            cr_prompt = EXAMPLE_AND_INSTRUCTION.format(
                format_example=format_example,
                filename=self.i_context.code_doc.filename,
            )
            len1 = len(iterative_code) if iterative_code else 0
            len2 = len(self.i_context.code_doc.content) if self.i_context.code_doc.content else 0
            logger.info(
                f"Code review and rewrite {self.i_context.code_doc.filename}: {i + 1}/{k} | len(iterative_code)={len1}, "
                f"len(self.i_context.code_doc.content)={len2}"
            )
            result, rewrited_code = await self.write_code_review_and_rewrite(
                context_prompt, cr_prompt, self.i_context.code_doc
            )
            if "LBTM" in result:
                iterative_code = rewrited_code
            elif "LGTM" in result:
                self.i_context.code_doc.content = iterative_code
                return self.i_context
        # code_rsp = await self._aask_v1(prompt, "code_rsp", OUTPUT_MAPPING)
        # self._save(context, filename, code)
        # 如果rewrited_code是None（原code perfect），那么直接返回code
        self.i_context.code_doc.content = iterative_code
        return self.i_context