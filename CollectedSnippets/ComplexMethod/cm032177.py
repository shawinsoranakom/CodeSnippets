def _process_text_fragments(self, text_fragments: List[TextFragment], current_iteration: int = 1) -> str:
        """处理文本片段，支持多次降重

        Args:
            text_fragments: 要处理的文本片段列表
            current_iteration: 当前是第几次降重迭代

        Returns:
            处理后的文本内容
        """
        self.chatbot[-1] = ["开始处理文本", f"第 {current_iteration}/{self.reduction_times} 次降重，共 {len(text_fragments)} 个片段"]
        yield from update_ui(chatbot=self.chatbot, history=self.history)

        # 重置处理结果，为当前迭代做准备
        self.processed_results = []
        self.failed_fragments = []

        # 一次性准备所有输入
        inputs_array, inputs_show_user_array, history_array = self._create_batch_inputs(text_fragments, current_iteration)

        # 对于单次调用的特殊处理 - 使用更强力的系统提示词
        if self.reduction_times == 1:
            sys_prompt = f"""你是一个伪装成人类科研学者的AI，能够将各种AI生成内容改写成人类学者常用的表达方式，让人类学者无法分辨。

你的任务是对学术文本进行深度改写，以彻底消除AI特征，使其具有真实人类学者的写作特点：

1. 打破AI常见的规整句式结构和词汇选择模式
2. 引入学术写作中的自然变化和不规则性
3. 使用多样化的句式和段落结构，避免明显的平衡性和规律性
4. 加入人类写作中常见的微小不完美之处，如段落长度变化、论述强调点不均等
5. 在维持核心论点的同时，完全重构表达方式
6. 适当使用学科领域内专家常用的表达习惯和术语
7. 确保文本读起来自然流畅，避免机械感
8. 打破AI生成内容常见的逻辑结构和表达套路
9. 根据文本内容，在保持专业性的基础上增加写作的特色和个性

对于每个文本片段，尽可能彻底地重构，使其无法被识别为AI生成。"""

            sys_prompt_array = [sys_prompt] * len(text_fragments)

        else:
            # 原有的多次迭代处理逻辑
            # 根据迭代次数调整系统提示词强度
            base_instruction = self.plugin_kwargs.get("advanced_arg", """你是一个人类科研工作者，请对以下学术文本进行彻底改写，以显著降低AI生成特征。具体要求如下：

1. 保持学术写作的严谨性和专业性
2. 维持原文的核心论述和逻辑框架
3. 优化句式结构：
   - 灵活运用主动句与被动句
   - 适当拆分复杂句式，提高可读性
   - 注意句式的多样性，避免重复模式
   - 打破AI常用的句式模板
4. 改善用词：
   - 使用更多学术语境下的同义词替换
   - 避免过于机械和规律性的连接词
   - 适当调整专业术语的表达方式
   - 增加词汇多样性，减少重复用词
5. 增强文本的学术特征：
   - 注重论证的严密性
   - 保持表达的客观性
   - 适度体现作者的学术见解
   - 避免过于完美和均衡的论述结构
6. 确保语言风格的一致性
7. 减少AI生成文本常见的套路和模式""")

            # 根据迭代次数增强强度
            if current_iteration == 1:
                # 第一次迭代使用基础强度
                instruction = base_instruction
                sys_prompt = f"""你是一个伪装成人类科研学者的AI，能够将各种AI生成内容改写成人类学者常用的表达方式，让人类学者无法分辨。请进行第{current_iteration}轮深度改写：

1. 严格保持学术写作规范
2. 维持原文的核心论述和逻辑框架
3. 通过优化句式结构和用词降低AI生成特征
4. 确保语言风格的一致性和专业性
5. 保持内容的客观性和准确性
6. 避免AI常见的套路化表达和过于完美的结构"""
            elif current_iteration == 2:
                # 第二次迭代使用中等强度
                instruction = base_instruction + """这是第二次改写，请进一步优化：

1. 更深入地调整句式结构，增加表达多样性
2. 在保持准确性的前提下，替换更多专业术语的表达方式
3. 优化段落结构，增强逻辑连贯性
4. 适当调整学术论证的表达方式
5. 打破AI生成内容的常见模式，如过于均衡的结构和规律性的表达方式"""
                sys_prompt = f"""你是一个伪装成人类科研学者的AI，能够将各种AI生成内容改写成人类学者常用的表达方式，让人类学者无法分辨。请进行第二轮改写：

1. 在保持严谨性的基础上，优化表达方式
2. 改善文本结构，提升学术论述的清晰度
3. 增强专业术语使用的灵活性
4. 确保论证过程的完整性和逻辑性
5. 进一步减少AI生成内容的特征和模式
6. 使文本表现出更自然、更人性化的写作风格"""
            else:
                # 第三次或更多次迭代使用高强度
                instruction = base_instruction + f"""这是第{current_iteration}次改写，需要在保持学术性的前提下彻底重构文本：

1. 全面重构句式，采用不同的表达策略
2. 系统性替换学术用语，保持专业准确性
3. 重组段落结构，优化论证层次
4. 深化学术观点的表达方式
5. 增强文本的逻辑严密性
6. 提升论述的专业深度
7. 确保不遗漏任何学术观点和论证要素
8. 适当使用学术表达技巧（如精准举例、恰当转折等），但不过分依赖比喻和类比
9. 彻底消除AI生成内容的特征，使文本具有真实学者的写作风格"""
                sys_prompt = f"""你是一个伪装成人类科研学者的AI，能够将各种AI生成内容改写成人类学者常用的表达方式，让人类学者无法分辨。请进行第{current_iteration}轮深度改写：

1. 在保持专业水准的前提下，彻底重构表达方式，引入长难句
2. 确保学术论证的严密性和完整性
3. 优化专业术语的运用
4. 提升文本的学术价值
5. 保持论述的逻辑性和连贯性
6. 适当使用少量学术表达技巧，提高文本说服力，但避免过度使用比喻和类比
7. 消除所有明显的AI生成痕迹，使文本更接近真实学者的写作风格"""

            sys_prompt_array = [sys_prompt] * len(text_fragments)

        # 调用LLM一次性处理所有片段
        response_collection = yield from request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency(
            inputs_array=inputs_array,
            inputs_show_user_array=inputs_show_user_array,
            llm_kwargs=self.llm_kwargs,
            chatbot=self.chatbot,
            history_array=history_array,
            sys_prompt_array=sys_prompt_array,
        )

        # 处理响应
        for j, frag in enumerate(text_fragments):
            try:
                llm_response = response_collection[j * 2 + 1]
                processed_text = self._extract_decision(llm_response)

                if processed_text and processed_text.strip():
                    self.processed_results.append({
                        'index': frag.fragment_index,
                        'content': processed_text
                    })
                else:
                    self.failed_fragments.append(frag)
                    self.processed_results.append({
                        'index': frag.fragment_index,
                        'content': frag.content
                    })
            except Exception as e:
                self.failed_fragments.append(frag)
                self.processed_results.append({
                    'index': frag.fragment_index,
                    'content': frag.content
                })

        # 按原始顺序合并结果
        self.processed_results.sort(key=lambda x: x['index'])
        final_content = "\n".join([item['content'] for item in self.processed_results])

        # 更新UI
        success_count = len(text_fragments) - len(self.failed_fragments)
        self.chatbot[-1] = ["当前阶段处理完成", f"第 {current_iteration}/{self.reduction_times} 次降重，成功处理 {success_count}/{len(text_fragments)} 个片段"]
        yield from update_ui(chatbot=self.chatbot, history=self.history)

        return final_content