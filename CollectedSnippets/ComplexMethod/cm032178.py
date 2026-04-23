def collect_section_contents(sections, parent_path=""):
                """递归收集章节内容，跳过参考文献部分"""
                for i, section in enumerate(sections):
                    current_path = f"{parent_path}/{i}" if parent_path else f"{i}"

                    # 检查是否为参考文献部分，如果是则跳过
                    if section.section_type == 'references' or section.title.lower() in ['references', '参考文献', 'bibliography', '文献']:
                        continue  # 跳过参考文献部分

                    # 只处理内容非空的章节
                    if section.content and section.content.strip():
                        # 使用增强的分割函数进行更细致的分割
                        fragments = self._breakdown_section_content(section.content)

                        for fragment_idx, fragment_content in enumerate(fragments):
                            if fragment_content.strip():
                                fragment_index = len(sections_to_process)
                                sections_to_process.append(TextFragment(
                                    content=fragment_content,
                                    fragment_index=fragment_index,
                                    total_fragments=0  # 临时值，稍后更新
                                ))

                                # 保存映射关系，用于稍后更新章节内容
                                # 为每个片段存储原始章节和片段索引信息
                                section_map[fragment_index] = (current_path, section, fragment_idx, len(fragments))

                    # 递归处理子章节
                    if section.subsections:
                        collect_section_contents(section.subsections, current_path)