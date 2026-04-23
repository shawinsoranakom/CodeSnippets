def _format_pubmed_content(self, child):
        """Extract structured reference info from PubMed XML"""
        def safe_find(path):
            node = child
            for p in path.split("/"):
                if node is None:
                    return None
                node = node.find(p)
            return node.text if node is not None and node.text else None

        title = safe_find("MedlineCitation/Article/ArticleTitle") or "No title"
        abstract = safe_find("MedlineCitation/Article/Abstract/AbstractText") or "No abstract available"
        journal = safe_find("MedlineCitation/Article/Journal/Title") or "Unknown Journal"
        volume = safe_find("MedlineCitation/Article/Journal/JournalIssue/Volume") or "-"
        issue = safe_find("MedlineCitation/Article/Journal/JournalIssue/Issue") or "-"
        pages = safe_find("MedlineCitation/Article/Pagination/MedlinePgn") or "-"

        # Authors
        authors = []
        for author in child.findall(".//AuthorList/Author"):
            lastname = safe_find("LastName") or ""
            forename = safe_find("ForeName") or ""
            fullname = f"{forename} {lastname}".strip()
            if fullname:
                authors.append(fullname)
        authors_str = ", ".join(authors) if authors else "Unknown Authors"

        # DOI
        doi = None
        for eid in child.findall(".//ArticleId"):
            if eid.attrib.get("IdType") == "doi":
                doi = eid.text
                break

        return (
            f"Title: {title}\n"
            f"Authors: {authors_str}\n"
            f"Journal: {journal}\n"
            f"Volume: {volume}\n"
            f"Issue: {issue}\n"
            f"Pages: {pages}\n"
            f"DOI: {doi or '-'}\n"
            f"Abstract: {abstract.strip()}"
        )