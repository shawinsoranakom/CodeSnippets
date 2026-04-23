def process_files(self, project_folder: str, file_paths: List[str]) -> Generator:
        """处理所有文件"""
        total_files = len(file_paths)
        self.chatbot.append([f"开始处理", f"总计 {total_files} 个文件"])
        yield from update_ui(chatbot=self.chatbot, history=self.history)

        # 1. 准备所有文件片段
        # 在 process_files 函数中：
        fragments = yield from self.prepare_fragments(project_folder, file_paths)
        if not fragments:
            self.chatbot.append(["处理失败", "没有可处理的文件内容"])
            return "没有可处理的文件内容"

        # 2. 批量处理所有文件片段
        self.chatbot.append([f"文件分析", f"共计 {len(fragments)} 个处理单元"])
        yield from update_ui(chatbot=self.chatbot, history=self.history)

        try:
            file_summaries = yield from self._process_fragments_batch(fragments)
        except Exception as e:
            self.chatbot.append(["处理错误", f"批处理过程失败：{str(e)}"])
            return "处理过程发生错误"

        # 3. 为每个文件生成整体总结
        self.chatbot.append(["生成总结", "正在汇总文件内容..."])
        yield from update_ui(chatbot=self.chatbot, history=self.history)

        # 处理每个文件的总结
        for rel_path, summaries in file_summaries.items():
            if len(summaries) > 1:  # 多片段文件需要生成整体总结
                sorted_summaries = sorted(summaries, key=lambda x: x['index'])
                if self.plugin_kwargs.get("advanced_arg"):

                    i_say = f'请按照用户要求对文件内容进行处理，用户要求为：{self.plugin_kwargs["advanced_arg"]}：'
                else:
                    i_say = f"请总结文件 {os.path.basename(rel_path)} 的主要内容，不超过500字。"

                try:
                    summary_texts = [s['summary'] for s in sorted_summaries]
                    response_collection = yield from request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency(
                        inputs_array=[i_say],
                        inputs_show_user_array=[f"生成 {rel_path} 的处理结果"],
                        llm_kwargs=self.llm_kwargs,
                        chatbot=self.chatbot,
                        history_array=[summary_texts],
                        sys_prompt_array=["你是一个优秀的助手，"],
                    )
                    self.file_summaries_map[rel_path] = response_collection[1]
                except Exception as e:
                    self.chatbot.append(["警告", f"文件 {rel_path} 总结生成失败：{str(e)}"])
                    self.file_summaries_map[rel_path] = "总结生成失败"
            else:  # 单片段文件直接使用其唯一的总结
                self.file_summaries_map[rel_path] = summaries[0]['summary']

        # 4. 生成最终总结
        if total_files == 1:
            return "文件数为1，此时不调用总结模块"
        else:
            try:
                # 收集所有文件的总结用于生成最终总结
                file_summaries_for_final = []
                for rel_path, summary in self.file_summaries_map.items():
                    file_summaries_for_final.append(f"文件 {rel_path} 的总结：\n{summary}")

                if self.plugin_kwargs.get("advanced_arg"):
                    final_summary_prompt = ("根据以下所有文件的总结内容，按要求进行综合处理：" +
                                            self.plugin_kwargs['advanced_arg'])
                else:
                    final_summary_prompt = "请根据以下所有文件的总结内容，生成最终的总结报告。"

                response_collection = yield from request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency(
                    inputs_array=[final_summary_prompt],
                    inputs_show_user_array=["生成最终总结报告"],
                    llm_kwargs=self.llm_kwargs,
                    chatbot=self.chatbot,
                    history_array=[file_summaries_for_final],
                    sys_prompt_array=["总结所有文件内容。"],
                    max_workers=1
                )

                return response_collection[1] if len(response_collection) > 1 else "生成总结失败"
            except Exception as e:
                self.chatbot.append(["错误", f"最终总结生成失败：{str(e)}"])
                return "生成总结失败"