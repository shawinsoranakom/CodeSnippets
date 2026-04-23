def _parse_paper_data(self, data: Dict) -> PaperMetadata:
        """解析Scopus API返回的数据

        Args:
            data: Scopus API返回的论文数据

        Returns:
            解析后的论文元数据
        """
        try:
            # 提取基本信息
            title = data.get("dc:title", "")

            # 提取作者信息
            authors = []
            if "author" in data:
                if isinstance(data["author"], list):
                    for author in data["author"]:
                        if "given-name" in author and "surname" in author:
                            authors.append(f"{author['given-name']} {author['surname']}")
                        elif "indexed-name" in author:
                            authors.append(author["indexed-name"])
                elif isinstance(data["author"], dict):
                    if "given-name" in data["author"] and "surname" in data["author"]:
                        authors.append(f"{data['author']['given-name']} {data['author']['surname']}")
                    elif "indexed-name" in data["author"]:
                        authors.append(data["author"]["indexed-name"])

            # 提取摘要
            abstract = data.get("dc:description", "")

            # 提取年份
            year = None
            if "prism:coverDate" in data:
                try:
                    year = int(data["prism:coverDate"][:4])
                except:
                    pass

            # 提取DOI
            doi = data.get("prism:doi")

            # 提取引用次数
            citations = data.get("citedby-count")
            if citations:
                try:
                    citations = int(citations)
                except:
                    citations = None

            # 提取期刊信息
            venue = data.get("prism:publicationName")

            # 提取机构信息
            institutions = []
            if "affiliation" in data:
                if isinstance(data["affiliation"], list):
                    for aff in data["affiliation"]:
                        if "affilname" in aff:
                            institutions.append(aff["affilname"])
                elif isinstance(data["affiliation"], dict):
                    if "affilname" in data["affiliation"]:
                        institutions.append(data["affiliation"]["affilname"])

            # 构建venue信息
            venue_info = {
                "issn": data.get("prism:issn"),
                "eissn": data.get("prism:eIssn"),
                "volume": data.get("prism:volume"),
                "issue": data.get("prism:issueIdentifier"),
                "page_range": data.get("prism:pageRange"),
                "article_number": data.get("article-number"),
                "publication_date": data.get("prism:coverDate")
            }

            return PaperMetadata(
                title=title,
                authors=authors,
                abstract=abstract,
                year=year,
                doi=doi,
                url=data.get("link", [{}])[0].get("@href"),
                citations=citations,
                venue=venue,
                institutions=institutions,
                venue_type="journal",
                venue_name=venue,
                venue_info=venue_info
            )

        except Exception as e:
            print(f"解析论文数据时发生错误: {str(e)}")
            return None