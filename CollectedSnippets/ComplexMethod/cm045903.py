def _add_chart_table(self):
        idx_xlsx_map = {}
        rel_pattern = re.compile(r"word/charts/_rels/chart(\d+)\.xml\.rels$")

        # 定义命名空间
        namespaces = {
            "r": "http://schemas.openxmlformats.org/package/2006/relationships"
        }

        # first pass: read relationships from rewindable byte buffer
        with zipfile.ZipFile(BytesIO(self._file_bytes), "r") as zf:
            for name in zf.namelist():
                match = rel_pattern.match(name)
                if match:
                    # 读取 .rels 文件内容
                    rels_content = zf.read(name)
                    # 解析 XML
                    rels_root = etree.fromstring(rels_content)

                    # 查找所有 Relationship 元素
                    for rel in rels_root.findall(
                        ".//r:Relationship", namespaces=namespaces
                    ):
                        target = rel.get("Target")
                        if target and target.endswith(".xlsx"):
                            path = Path(target)
                            idx_xlsx_map[path.name] = int(match.group(1))

        # second pass: again open buffer rather than original stream
        with zipfile.ZipFile(BytesIO(self._file_bytes), "r") as zf:
            for name in zf.namelist():
                if name.startswith("word/embeddings/"):
                    for path_name, chart_idx in idx_xlsx_map.items():
                        if name.endswith(path_name):
                            content = zf.read(name)
                            self.chart_list[chart_idx - 1]["content"] = (
                                html_table_from_excel_bytes(content)
                            )