def __call__(self, fnm, binary=None, from_page=0, to_page=10000000000, callback=None, **kwargs):
        if not binary:
            wb = Excel._load_excel_to_workbook(fnm)
        else:
            wb = Excel._load_excel_to_workbook(BytesIO(binary))
        total = 0
        for sheet_name in wb.sheetnames:
            total += Excel._get_actual_row_count(wb[sheet_name])
        res, fails, done = [], [], 0
        rn = 0
        flow_images = []
        pending_cell_images = []
        tables = []
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            images = Excel._extract_images_from_worksheet(ws, sheetname=sheet_name)
            if images:
                image_descriptions = vision_figure_parser_figure_xlsx_wrapper(images=images, callback=callback,
                                                                              **kwargs)
                if image_descriptions and len(image_descriptions) == len(images):
                    for i, bf in enumerate(image_descriptions):
                        images[i]["image_description"] = "\n".join(bf[0][1])
                    for img in images:
                        if img["span_type"] == "single_cell" and img.get("image_description"):
                            pending_cell_images.append(img)
                        else:
                            flow_images.append(img)

            try:
                rows = Excel._get_rows_limited(ws)
            except Exception as e:
                logging.warning(f"Skip sheet '{sheet_name}' due to rows access error: {e}")
                continue
            if not rows:
                continue
            headers, header_rows = self._parse_headers(ws, rows)
            if not headers:
                continue
            data = []
            for i, r in enumerate(rows[header_rows:]):
                rn += 1
                if rn - 1 < from_page:
                    continue
                if rn - 1 >= to_page:
                    break
                row_data = self._extract_row_data(ws, r, header_rows + i, len(headers))
                if row_data is None:
                    fails.append(str(i))
                    continue
                if self._is_empty_row(row_data):
                    continue
                data.append(row_data)
                done += 1
            if len(data) == 0:
                continue
            df = pd.DataFrame(data, columns=headers)
            for img in pending_cell_images:
                excel_row = img["row_from"] - 1
                excel_col = img["col_from"] - 1

                df_row_idx = excel_row - header_rows
                if df_row_idx < 0 or df_row_idx >= len(df):
                    flow_images.append(img)
                    continue

                if excel_col < 0 or excel_col >= len(df.columns):
                    flow_images.append(img)
                    continue

                col_name = df.columns[excel_col]

                if not df.iloc[df_row_idx][col_name]:
                    df.iat[df_row_idx, excel_col] = img["image_description"]
            res.append(df)
        for img in flow_images:
            tables.append(
                (
                    (
                        img["image"],  # Image.Image or LazyImage
                        [img["image_description"]]  # description list (must be list)
                    ),
                    [
                        (0, 0, 0, 0, 0)  # dummy position
                    ]
                )
            )
        callback(0.3, ("Extract records: {}~{}".format(from_page + 1, min(to_page, from_page + rn)) + (
            f"{len(fails)} failure, line: %s..." % (",".join(fails[:3])) if fails else "")))
        return res, tables