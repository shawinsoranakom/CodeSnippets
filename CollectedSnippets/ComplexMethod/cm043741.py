def parse_entry(entry):
            """Parse each entry in the response."""
            source = entry.get("_source", {})
            ciks = ",".join(source["ciks"]) if source.get("ciks") else None
            display_nammes = source.get("display_names", [])
            names: list = []
            tickers: list = []
            sics = ",".join(source.get("sics", []))
            for name in display_nammes:
                ticker = name.split("(")[1].split(")")[0].strip()
                tickers.append(ticker)
                _name = name.split("(")[0].strip()
                names.append(_name)

            output: dict = {}
            output["filing_date"] = source.get("file_date")
            output["period_ending"] = source.get("period_ending")
            output["symbol"] = ",".join(tickers).replace(" ", "")
            output["name"] = ",".join(names)
            output["cik"] = ciks
            output["sic"] = sics
            output["report_type"] = source.get("form")
            output["description"] = source.get("file_description")

            _id = entry.get("_id")
            root_url = (
                "https://www.sec.gov/Archives/edgar/data/"
                + source["ciks"][0]
                + "/"
                + source["adsh"].replace("-", "")
                + "/"
            )
            output["items"] = ",".join(source["items"]) if source.get("items") else None
            output["url"] = root_url + _id.split(":")[1]
            output["index_headers"] = (
                root_url + _id.split(":")[0] + "-index-headers.html"
            )
            output["complete_submission"] = root_url + _id.split(":")[0] + ".txt"
            output["metadata"] = (
                root_url + "MetaLinks.json"
                if output["report_type"].startswith("10-")
                or output["report_type"].startswith("8-")
                else None
            )
            output["financial_report"] = (
                root_url + "Financial_Report.xlsx"
                if output["report_type"].startswith("10-")
                or output["report_type"].startswith("8-")
                or output["report_type"] in ["N-CSR", "QRTLYRPT", "ANNLRPT"]
                else None
            )
            return output