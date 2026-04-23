def _format_papers(self, papers: List) -> str:
        """格式化论文列表，使用token限制控制长度"""
        formatted = []

        for i, paper in enumerate(papers, 1):
            # 只保留前三个作者
            authors = paper.authors[:3]
            if len(paper.authors) > 3:
                authors.append("et al.")

            # 构建所有可能的下载链接
            download_links = []

            # 添加arXiv链接
            if hasattr(paper, 'doi') and paper.doi:
                if paper.doi.startswith("10.48550/arXiv."):
                    # 从DOI中提取完整的arXiv ID
                    arxiv_id = paper.doi.split("arXiv.")[-1]
                    # 移除多余的点号并确保格式正确
                    arxiv_id = arxiv_id.replace("..", ".")  # 移除重复的点号
                    if arxiv_id.startswith("."):  # 移除开头的点号
                        arxiv_id = arxiv_id[1:]
                    if arxiv_id.endswith("."):  # 移除结尾的点号
                        arxiv_id = arxiv_id[:-1]

                    download_links.append(f"[arXiv PDF](https://arxiv.org/pdf/{arxiv_id}.pdf)")
                    download_links.append(f"[arXiv Page](https://arxiv.org/abs/{arxiv_id})")
                elif "arxiv.org/abs/" in paper.doi:
                    # 直接从URL中提取arXiv ID
                    arxiv_id = paper.doi.split("arxiv.org/abs/")[-1]
                    if "v" in arxiv_id:  # 移除版本号
                        arxiv_id = arxiv_id.split("v")[0]

                    download_links.append(f"[arXiv PDF](https://arxiv.org/pdf/{arxiv_id}.pdf)")
                    download_links.append(f"[arXiv Page](https://arxiv.org/abs/{arxiv_id})")
                else:
                    download_links.append(f"[DOI](https://doi.org/{paper.doi})")

            # 添加直接URL链接（如果存在且不同于前面的链接）
            if hasattr(paper, 'url') and paper.url:
                if not any(paper.url in link for link in download_links):
                    download_links.append(f"[Source]({paper.url})")

            # 构建下载链接字符串
            download_section = " | ".join(download_links) if download_links else "No direct download link available"

            # 构建来源信息
            source_info = []
            if hasattr(paper, 'venue_type') and paper.venue_type and paper.venue_type != 'preprint':
                source_info.append(f"Type: {paper.venue_type}")
            if hasattr(paper, 'venue_name') and paper.venue_name:
                source_info.append(f"Venue: {paper.venue_name}")

            # 添加IF指数和分区信息
            if hasattr(paper, 'if_factor') and paper.if_factor:
                source_info.append(f"IF: {paper.if_factor}")
            if hasattr(paper, 'cas_division') and paper.cas_division:
                source_info.append(f"中科院分区: {paper.cas_division}")
            if hasattr(paper, 'jcr_division') and paper.jcr_division:
                source_info.append(f"JCR分区: {paper.jcr_division}")

            if hasattr(paper, 'venue_info') and paper.venue_info:
                if paper.venue_info.get('journal_ref'):
                    source_info.append(f"Journal Reference: {paper.venue_info['journal_ref']}")
                if paper.venue_info.get('publisher'):
                    source_info.append(f"Publisher: {paper.venue_info['publisher']}")

            # 构建当前论文的格式化文本
            paper_text = (
                    f"{i}. **{paper.title}**\n" +
                    f"   Authors: {', '.join(authors)}\n" +
                    f"   Year: {paper.year}\n" +
                    f"   Citations: {paper.citations if paper.citations else 'N/A'}\n" +
                    (f"   Source: {'; '.join(source_info)}\n" if source_info else "") +
                    # 添加PubMed特有信息
                    (f"   MeSH Terms: {'; '.join(paper.mesh_terms)}\n" if hasattr(paper,
                                                                                  'mesh_terms') and paper.mesh_terms else "") +
                    f"   📥 PDF Downloads: {download_section}\n" +
                    f"   Abstract: {paper.abstract}\n"
            )

            formatted.append(paper_text)

        full_text = "\n".join(formatted)

        # 根据不同模型设置不同的token限制
        model_name = getattr(self, 'llm_kwargs', {}).get('llm_model', 'gpt-3.5-turbo')

        token_limit = model_info[model_name]['max_token'] * 3 // 4
        # 使用token限制控制长度
        return cut_from_end_to_satisfy_token_limit(full_text, limit=token_limit, reserve_token=0, llm_model=model_name)