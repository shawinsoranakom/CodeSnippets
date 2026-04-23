def _process_fragments_batch(self, fragments: List[FileFragment]) -> Generator:
        """批量处理文件片段"""
        from collections import defaultdict
        batch_size = 64  # 每批处理的片段数
        max_retries = 3  # 最大重试次数
        retry_delay = 5  # 重试延迟（秒）
        results = defaultdict(list)

        # 按批次处理
        for i in range(0, len(fragments), batch_size):
            batch = fragments[i:i + batch_size]

            inputs_array, inputs_show_user_array, history_array = self._create_batch_inputs(batch)
            sys_prompt_array = ["请总结以下内容："] * len(batch)

            # 添加重试机制
            for retry in range(max_retries):
                try:
                    response_collection = yield from request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency(
                        inputs_array=inputs_array,
                        inputs_show_user_array=inputs_show_user_array,
                        llm_kwargs=self.llm_kwargs,
                        chatbot=self.chatbot,
                        history_array=history_array,
                        sys_prompt_array=sys_prompt_array,
                    )

                    # 处理响应
                    for j, frag in enumerate(batch):
                        summary = response_collection[j * 2 + 1]
                        if summary and summary.strip():
                            results[frag.rel_path].append({
                                'index': frag.fragment_index,
                                'summary': summary,
                                'total': frag.total_fragments
                            })
                    break  # 成功处理，跳出重试循环

                except Exception as e:
                    if retry == max_retries - 1:  # 最后一次重试失败
                        for frag in batch:
                            self.failed_files.append((frag.file_path, f"处理失败：{str(e)}"))
                    else:
                        yield from update_ui(self.chatbot.append([f"批次处理失败，{retry_delay}秒后重试...", str(e)]))
                        time.sleep(retry_delay)

        return results