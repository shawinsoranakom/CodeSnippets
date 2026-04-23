def _breakdown_section_content(self, content: str) -> List[str]:
        """对文本内容进行分割与合并

        主要按段落进行组织，只合并较小的段落以减少片段数量
        保留原始段落结构，不对长段落进行强制分割
        针对中英文设置不同的阈值，因为字符密度不同
        """
        # 先按段落分割文本
        paragraphs = content.split('\n\n')

        # 检测语言类型
        chinese_char_count = sum(1 for char in content if '\u4e00' <= char <= '\u9fff')
        is_chinese_text = chinese_char_count / max(1, len(content)) > 0.3

        # 根据语言类型设置不同的阈值（只用于合并小段落）
        if is_chinese_text:
            # 中文文本：一个汉字就是一个字符，信息密度高
            min_chunk_size = 300  # 段落合并的最小阈值
            target_size = 800  # 理想的段落大小
        else:
            # 英文文本：一个单词由多个字符组成，信息密度低
            min_chunk_size = 600  # 段落合并的最小阈值
            target_size = 1600  # 理想的段落大小

        # 1. 只合并小段落，不对长段落进行分割
        result_fragments = []
        current_chunk = []
        current_length = 0

        for para in paragraphs:
            # 如果段落太小且不会超过目标大小，则合并
            if len(para) < min_chunk_size and current_length + len(para) <= target_size:
                current_chunk.append(para)
                current_length += len(para)
            # 否则，创建新段落
            else:
                # 如果当前块非空且与当前段落无关，先保存它
                if current_chunk and current_length > 0:
                    result_fragments.append('\n\n'.join(current_chunk))

                # 当前段落作为新块
                current_chunk = [para]
                current_length = len(para)

            # 如果当前块大小已接近目标大小，保存并开始新块
            if current_length >= target_size:
                result_fragments.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_length = 0

        # 保存最后一个块
        if current_chunk:
            result_fragments.append('\n\n'.join(current_chunk))

        # 2. 处理可能过大的片段（确保不超过token限制）
        final_fragments = []
        max_token = self._get_token_limit()

        for fragment in result_fragments:
            # 检查fragment是否可能超出token限制
            # 根据语言类型调整token估算
            if is_chinese_text:
                estimated_tokens = len(fragment) / 1.5  # 中文每个token约1-2个字符
            else:
                estimated_tokens = len(fragment) / 4  # 英文每个token约4个字符

            if estimated_tokens > max_token:
                # 即使可能超出限制，也尽量保持段落的完整性
                # 使用breakdown_text但设置更大的限制来减少分割
                larger_limit = max_token * 0.95  # 使用95%的限制
                sub_fragments = breakdown_text_to_satisfy_token_limit(
                    txt=fragment,
                    limit=larger_limit,
                    llm_model=self.llm_kwargs['llm_model']
                )
                final_fragments.extend(sub_fragments)
            else:
                final_fragments.append(fragment)

        return final_fragments