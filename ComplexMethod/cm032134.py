def _parse_article(self, article: ET.Element) -> PaperMetadata:
        """解析PubMed文章XML

        Args:
            article: XML元素

        Returns:
            解析后的论文数据
        """
        try:
            # 提取基本信息
            pmid = article.find(".//PMID").text
            article_meta = article.find(".//Article")

            # 获取标题
            title = article_meta.find(".//ArticleTitle")
            title = title.text if title is not None else ""

            # 获取作者列表
            authors = []
            author_list = article_meta.findall(".//Author")
            for author in author_list:
                last_name = author.find("LastName")
                fore_name = author.find("ForeName")
                if last_name is not None and fore_name is not None:
                    authors.append(f"{fore_name.text} {last_name.text}")
                elif last_name is not None:
                    authors.append(last_name.text)

            # 获取摘要
            abstract = article_meta.find(".//Abstract/AbstractText")
            abstract = abstract.text if abstract is not None else ""

            # 获取发表年份
            pub_date = article_meta.find(".//PubDate/Year")
            year = int(pub_date.text) if pub_date is not None else None

            # 获取DOI
            doi = article.find(".//ELocationID[@EIdType='doi']")
            doi = doi.text if doi is not None else None

            # 获取期刊信息
            journal = article_meta.find(".//Journal")
            if journal is not None:
                journal_title = journal.find(".//Title")
                venue = journal_title.text if journal_title is not None else None

                # 获取期刊详细信息
                venue_info = {
                    'issn': journal.findtext(".//ISSN"),
                    'volume': journal.findtext(".//Volume"),
                    'issue': journal.findtext(".//Issue"),
                    'pub_date': journal.findtext(".//PubDate/MedlineDate") or
                               f"{journal.findtext('.//PubDate/Year', '')}-{journal.findtext('.//PubDate/Month', '')}"
                }
            else:
                venue = None
                venue_info = {}

            # 获取机构信息
            institutions = []
            affiliations = article_meta.findall(".//Affiliation")
            for affiliation in affiliations:
                if affiliation is not None and affiliation.text:
                    institutions.append(affiliation.text)

            return PaperMetadata(
                title=title,
                authors=authors,
                abstract=abstract,
                year=year,
                doi=doi,
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
                citations=None,  # PubMed API不直接提供引用数据
                venue=venue,
                institutions=institutions,
                venue_type="journal",
                venue_name=venue,
                venue_info=venue_info,
                source='pubmed'  # 添加来源标记
            )

        except Exception as e:
            print(f"解析文章时发生错误: {str(e)}")
            return None