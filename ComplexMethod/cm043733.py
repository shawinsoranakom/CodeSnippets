def _download_index_headers(
        self,
    ):  # pylint: disable=too-many-branches, too-many-statements, too-many-locals
        """Download the index headers table."""
        # pylint: disable=import-outside-toplevel
        import re  # noqa
        from bs4 import BeautifulSoup

        try:
            if not self._index_headers_download:
                response = self.download_file(
                    self._index_headers_url, False, self._use_cache
                )
                self._index_headers_download = response
            else:
                response = self._index_headers_download

            soup = BeautifulSoup(response, "html.parser")
            text = soup.find("pre").text

            def document_to_dict(doc):
                """Convert the document section to a dictionary."""
                doc_dict: dict = {}
                doc_dict["type"] = re.search(r"<TYPE>(.*?)\n", doc).group(1).strip()  # type: ignore
                doc_dict["sequence"] = re.search(r"<SEQUENCE>(.*?)\n", doc).group(1).strip()  # type: ignore
                doc_dict["filename"] = re.search(r"<FILENAME>(.*?)\n", doc).group(1).strip()  # type: ignore
                description_match = re.search(r"<DESCRIPTION>(.*?)\n", doc)

                if description_match:
                    doc_dict["description"] = description_match.group(1).strip()

                url = self.base_url + doc_dict["filename"]
                doc_dict["url"] = url

                return doc_dict

            # Isolate each document by tag
            documents = re.findall(r"<DOCUMENT>.*?</DOCUMENT>", text, re.DOTALL)
            # Convert each document to a dictionary
            document_dicts = [document_to_dict(doc) for doc in documents]

            if document_dicts:
                self._document_urls = document_dicts

            lines = text.split("\n")
            n_items = 0

            for line in lines:
                if ":" not in line:
                    continue

                value = line.split(":")[1].strip()

                if n_items == 9:
                    break

                if "CONFORMED PERIOD OF REPORT" in line:
                    as_of_date = value
                    self._period_ending = (
                        as_of_date[:4] + "-" + as_of_date[4:6] + "-" + as_of_date[6:]
                    )
                elif "FILED AS OF DATE" in line:
                    filing_date = value
                    self._filing_date = (
                        filing_date[:4] + "-" + filing_date[4:6] + "-" + filing_date[6:]
                    )
                    n_items += 1
                elif "COMPANY CONFORMED NAME" in line:
                    self._name = value
                    n_items += 1
                elif "CONFORMED SUBMISSION TYPE" in line:
                    self._document_type = value
                    n_items += 1
                elif "CENTRAL INDEX KEY" in line:
                    self._cik = value
                    n_items += 1
                elif "STANDARD INDUSTRIAL CLASSIFICATION" in line:
                    self._sic = value
                    n_items += 1
                elif "ORGANIZATION NAME" in line:
                    self._sic_organization_name = value
                    n_items += 1
                elif "FISCAL YEAR END" in line:
                    fy = value
                    self._fiscal_year_end = fy[:2] + "-" + fy[2:]
                    n_items += 1
                # There might be two lines of ITEM INFORMATION
                elif "ITEM INFORMATION" in line:
                    info = value
                    self._description = (
                        self._description + "; " + info if self._description else info
                    )
                    n_items += 1
                continue

        except Exception as e:
            raise RuntimeError(
                f"Failed to download and read the index headers table: {e}"
            ) from e