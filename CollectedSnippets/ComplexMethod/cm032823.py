def chunk(filename, binary=None, from_page=0, to_page=10000000000, lang="Chinese", callback=None, **kwargs):
    """
    Excel and csv(txt) format files are supported.
    For csv or txt file, the delimiter between columns is TAB.
    The first line must be column headers.
    Column headers must be meaningful terms inorder to make our NLP model understanding.
    It's good to enumerate some synonyms using slash '/' to separate, and even better to
    enumerate values using brackets like 'gender/sex(male, female)'.
    Here are some examples for headers:
        1. supplier/vendor\tcolor(yellow, red, brown)\tgender/sex(male, female)\tsize(M,L,XL,XXL)
        2. 姓名/名字\t电话/手机/微信\t最高学历（高中，职高，硕士，本科，博士，初中，中技，中专，专科，专升本，MPA，MBA，EMBA）

    Every row in table will be treated as a chunk.
    """
    tbls = []
    is_english = lang.lower() == "english"
    if re.search(r"\.xlsx?$", filename, re.IGNORECASE):
        callback(0.1, "Start to parse.")
        excel_parser = Excel()
        dfs, tbls = excel_parser(filename, binary, from_page=from_page, to_page=to_page, callback=callback, **kwargs)
    elif re.search(r"\.txt$", filename, re.IGNORECASE):
        callback(0.1, "Start to parse.")
        txt = get_text(filename, binary)
        lines = txt.split("\n")
        fails = []
        headers = lines[0].split(kwargs.get("delimiter", "\t"))
        rows = []
        for i, line in enumerate(lines[1:]):
            if i < from_page:
                continue
            if i >= to_page:
                break
            row = [field for field in line.split(kwargs.get("delimiter", "\t"))]
            if len(row) != len(headers):
                fails.append(str(i))
                continue
            rows.append(row)

        callback(0.3, ("Extract records: {}~{}".format(from_page, min(len(lines), to_page)) + (
            f"{len(fails)} failure, line: %s..." % (",".join(fails[:3])) if fails else "")))

        dfs = [pd.DataFrame(np.array(rows), columns=headers)]
    elif re.search(r"\.csv$", filename, re.IGNORECASE):
        callback(0.1, "Start to parse.")
        txt = get_text(filename, binary)
        delimiter = kwargs.get("delimiter", ",")

        reader = csv.reader(io.StringIO(txt), delimiter=delimiter)
        all_rows = list(reader)
        if not all_rows:
            raise ValueError("Empty CSV file")

        headers = all_rows[0]
        fails = []
        rows = []

        for i, row in enumerate(all_rows[1 + from_page: 1 + to_page]):
            if len(row) != len(headers):
                fails.append(str(i + from_page))
                continue
            rows.append(row)

        callback(
            0.3,
            (f"Extract records: {from_page}~{from_page + len(rows)}" +
             (f"{len(fails)} failure, line: {','.join(fails[:3])}..." if fails else ""))
        )

        dfs = [pd.DataFrame(rows, columns=headers)]
    else:
        raise NotImplementedError("file type not supported yet(excel, text, csv supported)")

    res = []
    PY = Pinyin()
    # Field type suffixes for database columns
    # Maps data types to their database field suffixes
    fields_map = {"text": "_tks", "int": "_long", "keyword": "_kwd", "float": "_flt", "datetime": "_dt", "bool": "_kwd"}
    for df in dfs:
        for n in ["id", "_id", "index", "idx"]:
            if n in df.columns:
                del df[n]
        clmns = df.columns.values
        if len(clmns) != len(set(clmns)):
            col_counts = Counter(clmns)
            duplicates = [col for col, count in col_counts.items() if count > 1]
            if duplicates:
                raise ValueError(f"Duplicate column names detected: {duplicates}\nFrom: {clmns}")

        txts = list(copy.deepcopy(clmns))
        py_clmns = [PY.get_pinyins(re.sub(r"(/.*|（[^（）]+?）|\([^()]+?\))", "", str(n)), "_")[0] for n in clmns]
        clmn_tys = []
        for j in range(len(clmns)):
            cln, ty = column_data_type(df[clmns[j]])
            clmn_tys.append(ty)
            df[clmns[j]] = cln
            if ty == "text":
                txts.extend([str(c) for c in cln if c])
        clmns_map = [(py_clmns[i].lower() + fields_map[clmn_tys[i]], str(clmns[i]).replace("_", " ")) for i in
                     range(len(clmns))]
        # For Infinity/OceanBase: Use original column names as keys since they're stored in chunk_data JSON
        # For ES/OS: Use full field names with type suffixes (e.g., url_kwd, body_tks)
        if settings.DOC_ENGINE_INFINITY or settings.DOC_ENGINE_OCEANBASE:
            # For Infinity/OceanBase: key = original column name, value = display name
            field_map = {py_clmns[i].lower(): str(clmns[i]).replace("_", " ") for i in range(len(clmns))}
        else:
            # For ES/OS: key = typed field name, value = display name
            field_map = {k: v for k, v in clmns_map}
        logging.debug(f"Field map: {field_map}")
        KnowledgebaseService.update_parser_config(kwargs["kb_id"], {"field_map": field_map})

        eng = lang.lower() == "english"  # is_english(txts)
        for ii, row in df.iterrows():
            d = {"docnm_kwd": filename, "title_tks": rag_tokenizer.tokenize(re.sub(r"\.[a-zA-Z]+$", "", filename))}
            row_fields = []
            data_json = {}  # For Infinity: Store all columns in a JSON object
            for j in range(len(clmns)):
                if row[clmns[j]] is None:
                    continue
                if not str(row[clmns[j]]):
                    continue
                if not isinstance(row[clmns[j]], pd.Series) and pd.isna(row[clmns[j]]):
                    continue
                # For Infinity/OceanBase: Store in chunk_data JSON column
                # For Elasticsearch/OpenSearch: Store as individual fields with type suffixes
                if settings.DOC_ENGINE_INFINITY or settings.DOC_ENGINE_OCEANBASE:
                    data_json[str(clmns[j])] = row[clmns[j]]
                else:
                    fld = clmns_map[j][0]
                    d[fld] = row[clmns[j]] if clmn_tys[j] != "text" else rag_tokenizer.tokenize(row[clmns[j]])
                row_fields.append((clmns[j], row[clmns[j]]))
            if not row_fields:
                continue
            # Add the data JSON field to the document (for Infinity/OceanBase)
            if settings.DOC_ENGINE_INFINITY or settings.DOC_ENGINE_OCEANBASE:
                d["chunk_data"] = data_json
            # Format as a structured text for better LLM comprehension
            # Format each field as "- Field Name: Value" on separate lines
            formatted_text = "\n".join([f"- {field}: {value}" for field, value in row_fields])
            tokenize(d, formatted_text, eng)
            res.append(d)
        if tbls:
            doc = {"docnm_kwd": filename, "title_tks": rag_tokenizer.tokenize(re.sub(r"\.[a-zA-Z]+$", "", filename))}
            res.extend(tokenize_table(tbls, doc, is_english))
    callback(0.35, "")

    return res