def _load_cell_image_mappings(self):
        if self.cell_image_map:
            return self.cell_image_map

        if self.zf is None:
            return {}
        cell_image_embed_to_name = {}
        cellimages_path = "xl/cellimages.xml"
        rels_path = "xl/_rels/cellimages.xml.rels"
        if (
            cellimages_path not in self.zf.namelist()
            or rels_path not in self.zf.namelist()
        ):
            return {}

        try:
            with self.zf.open(cellimages_path) as f:
                root = ET.parse(f).getroot()

            ns = {
                "xdr": "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing",
                "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
                "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
                "etc": "http://www.wps.cn/officeDocument/2017/etCustomData",
            }

            for cell_image in root.findall(".//etc:cellImage", ns):
                c_nv_pr = cell_image.find(".//xdr:cNvPr", ns)
                blip = cell_image.find(".//a:blip", ns)
                if c_nv_pr is None or blip is None:
                    continue

                image_name = c_nv_pr.attrib.get("name")
                embed_id = blip.attrib.get(f'{{{ns["r"]}}}embed')
                if image_name and embed_id:
                    cell_image_embed_to_name[embed_id] = image_name

            with self.zf.open(rels_path) as f:
                rel_root = ET.parse(f).getroot()

            rel_ns = {
                "pr": "http://schemas.openxmlformats.org/package/2006/relationships"
            }
            for rel in rel_root.findall("pr:Relationship", rel_ns):
                rel_id = rel.attrib.get("Id")
                target = rel.attrib.get("Target")
                if rel_id and target:
                    image_name = cell_image_embed_to_name.get(rel_id)
                    if not image_name:
                        logger.warning(
                            f"跳过缺少 cellImage 名称映射的关系: {rel_id}"
                        )
                        continue
                    self.cell_image_map[image_name] = target

        except Exception as e:
            logger.warning(f"解析 cellimages 映射失败: {e}")
            return {}

        return self.cell_image_map