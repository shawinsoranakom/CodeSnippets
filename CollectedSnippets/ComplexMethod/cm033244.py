async def use_sql(question, field_map, tenant_id, chat_mdl, quota=True, kb_ids=None):
    logging.debug(f"use_sql: Question: {question}")

    # Determine which document engine we're using
    if settings.DOC_ENGINE_INFINITY:
        doc_engine = "infinity"
    elif settings.DOC_ENGINE_OCEANBASE:
        doc_engine = "oceanbase"
    else:
        doc_engine = "es"

    # Construct the full table name
    # For Elasticsearch: ragflow_{tenant_id} (kb_id is in WHERE clause)
    # For Infinity: ragflow_{tenant_id}_{kb_id} (each KB has its own table)
    base_table = index_name(tenant_id)
    if doc_engine == "infinity" and kb_ids and len(kb_ids) == 1:
        # Infinity: append kb_id to table name
        table_name = f"{base_table}_{kb_ids[0]}"
        logging.debug(f"use_sql: Using Infinity table name: {table_name}")
    else:
        # Elasticsearch/OpenSearch: use base index name
        table_name = base_table
        logging.debug(f"use_sql: Using ES/OS table name: {table_name}")

    expected_doc_name_column = "docnm" if doc_engine == "infinity" else "docnm_kwd"

    def has_source_columns(columns):
        normalized_names = {str(col.get("name", "")).lower() for col in columns}
        return "doc_id" in normalized_names and bool({"docnm_kwd", "docnm"} & normalized_names)

    def is_aggregate_sql(sql_text):
        return bool(re.search(r"(count|sum|avg|max|min|distinct)\s*\(", (sql_text or "").lower()))

    def normalize_sql(sql):
        logging.debug(f"use_sql: Raw SQL from LLM: {repr(sql[:500])}")
        # Remove think blocks if present (format: </think>...)
        sql = re.sub(r"</think>\n.*?\n\s*", "", sql, flags=re.DOTALL)
        sql = re.sub(r"思考\n.*?\n", "", sql, flags=re.DOTALL)
        # Remove markdown code blocks (```sql ... ```)
        sql = re.sub(r"```(?:sql)?\s*", "", sql, flags=re.IGNORECASE)
        sql = re.sub(r"```\s*$", "", sql, flags=re.IGNORECASE)
        # Remove trailing semicolon that ES SQL parser doesn't like
        return sql.rstrip().rstrip(';').strip()

    def add_kb_filter(sql):
        # Add kb_id filter for ES/OS only (Infinity already has it in table name)
        if doc_engine == "infinity" or not kb_ids:
            return sql

        # Build kb_filter: single KB or multiple KBs with OR
        if len(kb_ids) == 1:
            kb_filter = f"kb_id = '{kb_ids[0]}'"
        else:
            kb_filter = "(" + " OR ".join([f"kb_id = '{kb_id}'" for kb_id in kb_ids]) + ")"

        if "where " not in sql.lower():
            o = sql.lower().split("order by")
            if len(o) > 1:
                sql = o[0] + f" WHERE {kb_filter}  order by " + o[1]
            else:
                sql += f" WHERE {kb_filter}"
        elif "kb_id =" not in sql.lower() and "kb_id=" not in sql.lower():
            sql = re.sub(r"\bwhere\b ", f"where {kb_filter} and ", sql, flags=re.IGNORECASE)
        return sql

    def is_row_count_question(q: str) -> bool:
        q = (q or "").lower()
        if not re.search(r"\bhow many rows\b|\bnumber of rows\b|\brow count\b", q):
            return False
        return bool(re.search(r"\bdataset\b|\btable\b|\bspreadsheet\b|\bexcel\b", q))

    # Generate engine-specific SQL prompts
    if doc_engine == "infinity":
        # Build Infinity prompts with JSON extraction context
        json_field_names = list(field_map.keys())
        row_count_override = (
            f"SELECT COUNT(*) AS rows FROM {table_name}"
            if is_row_count_question(question)
            else None
        )
        sys_prompt = """You are a Database Administrator. Write SQL for a table with JSON 'chunk_data' column.

JSON Extraction: json_extract_string(chunk_data, '$.FieldName')
Numeric Cast: CAST(json_extract_string(chunk_data, '$.FieldName') AS INTEGER/FLOAT)
NULL Check: json_extract_isnull(chunk_data, '$.FieldName') == false

RULES:
1. Use EXACT field names (case-sensitive) from the list below
2. For SELECT: include doc_id, docnm, and json_extract_string() for requested fields
3. For COUNT: use COUNT(*) or COUNT(DISTINCT json_extract_string(...))
4. Add AS alias for extracted field names
5. DO NOT select 'content' field
6. Only add NULL check (json_extract_isnull() == false) in WHERE clause when:
   - Question asks to "show me" or "display" specific columns
   - Question mentions "not null" or "excluding null"
   - Add NULL check for count specific column
   - DO NOT add NULL check for COUNT(*) queries (COUNT(*) counts all rows including nulls)
7. Output ONLY the SQL, no explanations"""
        user_prompt = """Table: {}
Fields (EXACT case): {}
{}
Question: {}
Write SQL using json_extract_string() with exact field names. Include doc_id, docnm for data queries. Only SQL.""".format(
            table_name,
            ", ".join(json_field_names),
            "\n".join([f"  - {field}" for field in json_field_names]),
            question
        )
    elif doc_engine == "oceanbase":
        # Build OceanBase prompts with JSON extraction context
        json_field_names = list(field_map.keys())
        row_count_override = (
            f"SELECT COUNT(*) AS rows FROM {table_name}"
            if is_row_count_question(question)
            else None
        )
        sys_prompt = """You are a Database Administrator. Write SQL for a table with JSON 'chunk_data' column.

JSON Extraction: json_extract_string(chunk_data, '$.FieldName')
Numeric Cast: CAST(json_extract_string(chunk_data, '$.FieldName') AS INTEGER/FLOAT)
NULL Check: json_extract_isnull(chunk_data, '$.FieldName') == false

RULES:
1. Use EXACT field names (case-sensitive) from the list below
2. For SELECT: include doc_id, docnm_kwd, and json_extract_string() for requested fields
3. For COUNT: use COUNT(*) or COUNT(DISTINCT json_extract_string(...))
4. Add AS alias for extracted field names
5. DO NOT select 'content' field
6. Only add NULL check (json_extract_isnull() == false) in WHERE clause when:
   - Question asks to "show me" or "display" specific columns
   - Question mentions "not null" or "excluding null"
   - Add NULL check for count specific column
   - DO NOT add NULL check for COUNT(*) queries (COUNT(*) counts all rows including nulls)
7. Output ONLY the SQL, no explanations"""
        user_prompt = """Table: {}
Fields (EXACT case): {}
{}
Question: {}
Write SQL using json_extract_string() with exact field names. Include doc_id, docnm_kwd for data queries. Only SQL.""".format(
            table_name,
            ", ".join(json_field_names),
            "\n".join([f"  - {field}" for field in json_field_names]),
            question
        )
    else:
        # Build ES/OS prompts with direct field access
        row_count_override = None
        sys_prompt = """You are a Database Administrator. Write SQL queries.

RULES:
1. Use EXACT field names from the schema below (e.g., product_tks, not product)
2. Quote field names starting with digit: "123_field"
3. Add IS NOT NULL in WHERE clause when:
   - Question asks to "show me" or "display" specific columns
4. Include doc_id/docnm in non-aggregate statement
5. Output ONLY the SQL, no explanations"""
        user_prompt = """Table: {}
Available fields:
{}
Question: {}
Write SQL using exact field names above. Include doc_id, docnm_kwd for data queries. Only SQL.""".format(
            table_name,
            "\n".join([f"  - {k} ({v})" for k, v in field_map.items()]),
            question
        )

    tried_times = 0

    async def get_table(custom_user_prompt=None):
        nonlocal sys_prompt, user_prompt, question, tried_times, row_count_override
        if row_count_override and custom_user_prompt is None:
            sql = row_count_override
        else:
            prompt = custom_user_prompt if custom_user_prompt is not None else user_prompt
            sql = await chat_mdl.async_chat(sys_prompt, [{"role": "user", "content": prompt}], {"temperature": 0.06})
        sql = normalize_sql(sql)
        sql = add_kb_filter(sql)

        logging.debug(f"{question} get SQL(refined): {sql}")
        tried_times += 1
        logging.debug(f"use_sql: Executing SQL retrieval (attempt {tried_times})")
        tbl = settings.retriever.sql_retrieval(sql, format="json")
        if tbl is None:
            logging.debug("use_sql: SQL retrieval returned None")
            return None, sql
        logging.debug(f"use_sql: SQL retrieval completed, got {len(tbl.get('rows', []))} rows")
        return tbl, sql

    async def repair_table_for_missing_source_columns(previous_sql):
        if doc_engine in ("infinity", "oceanbase"):
            json_field_names = list(field_map.keys())
            repair_prompt = """Table name: {};
JSON fields available in 'chunk_data' column (use exact names):
{}

Question: {}
Previous SQL:
{}

The previous SQL result is missing required source columns for citations.
Rewrite SQL to keep the same query intent and include doc_id and {} in the SELECT list.
For extracted JSON fields, use json_extract_string(chunk_data, '$.field_name').
Return ONLY SQL.""".format(
                table_name,
                "\n".join([f"  - {field}" for field in json_field_names]),
                question,
                previous_sql,
                expected_doc_name_column
            )
        else:
            repair_prompt = """Table name: {}
Available fields:
{}

Question: {}
Previous SQL:
{}

The previous SQL result is missing required source columns for citations.
Rewrite SQL to keep the same query intent and include doc_id and docnm_kwd in the SELECT list.
Return ONLY SQL.""".format(
                table_name,
                "\n".join([f"  - {k} ({v})" for k, v in field_map.items()]),
                question,
                previous_sql
            )
        return await get_table(custom_user_prompt=repair_prompt)

    try:
        tbl, sql = await get_table()
        logging.debug(f"use_sql: Initial SQL execution SUCCESS. SQL: {sql}")
        logging.debug(f"use_sql: Retrieved {len(tbl.get('rows', []))} rows, columns: {[c['name'] for c in tbl.get('columns', [])]}")
    except Exception as e:
        logging.warning(f"use_sql: Initial SQL execution FAILED with error: {e}")
        # Build retry prompt with error information
        if doc_engine in ("infinity", "oceanbase"):
            # Build Infinity error retry prompt
            json_field_names = list(field_map.keys())
            user_prompt = """
Table name: {};
JSON fields available in 'chunk_data' column (use these exact names in json_extract_string):
{}

Question: {}
Please write the SQL using json_extract_string(chunk_data, '$.field_name') with the field names from the list above. Only SQL, no explanations.


The SQL error you provided last time is as follows:
{}

Please correct the error and write SQL again using json_extract_string(chunk_data, '$.field_name') syntax with the correct field names. Only SQL, no explanations.
""".format(table_name, "\n".join([f"  - {field}" for field in json_field_names]), question, e)
        else:
            # Build ES/OS error retry prompt
            user_prompt = """
        Table name: {};
        Table of database fields are as follows (use the field names directly in SQL):
        {}

        Question are as follows:
        {}
        Please write the SQL using the exact field names above, only SQL, without any other explanations or text.


        The SQL error you provided last time is as follows:
        {}

        Please correct the error and write SQL again using the exact field names above, only SQL, without any other explanations or text.
        """.format(table_name, "\n".join([f"{k} ({v})" for k, v in field_map.items()]), question, e)
        try:
            tbl, sql = await get_table()
            logging.debug(f"use_sql: Retry SQL execution SUCCESS. SQL: {sql}")
            logging.debug(f"use_sql: Retrieved {len(tbl.get('rows', []))} rows on retry")
        except Exception:
            logging.error("use_sql: Retry SQL execution also FAILED, returning None")
            return

    if len(tbl["rows"]) == 0:
        logging.warning(f"use_sql: No rows returned from SQL query, returning None. SQL: {sql}")
        return None

    if not is_aggregate_sql(sql) and not has_source_columns(tbl.get("columns", [])):
        logging.warning(f"use_sql: Non-aggregate SQL missing required source columns; retrying once. SQL: {sql}")
        try:
            repaired_tbl, repaired_sql = await repair_table_for_missing_source_columns(sql)
            if (
                repaired_tbl
                and len(repaired_tbl.get("rows", [])) > 0
                and has_source_columns(repaired_tbl.get("columns", []))
            ):
                tbl, sql = repaired_tbl, repaired_sql
                logging.info(f"use_sql: Source-column SQL repair succeeded. SQL: {sql}")
            else:
                logging.warning(f"use_sql: Source-column SQL repair did not provide required columns. Repaired SQL: {repaired_sql}")
        except Exception as e:
            logging.warning(f"use_sql: Source-column SQL repair failed, returning best-effort answer. Error: {e}")

    logging.debug(f"use_sql: Proceeding with {len(tbl['rows'])} rows to build answer")

    docid_idx = set([ii for ii, c in enumerate(tbl["columns"]) if c["name"].lower() == "doc_id"])
    doc_name_idx = set([ii for ii, c in enumerate(tbl["columns"]) if c["name"].lower() in ["docnm_kwd", "docnm"]])

    logging.debug(f"use_sql: All columns: {[(i, c['name']) for i, c in enumerate(tbl['columns'])]}")
    logging.debug(f"use_sql: docid_idx={docid_idx}, doc_name_idx={doc_name_idx}")

    column_idx = [ii for ii in range(len(tbl["columns"])) if ii not in (docid_idx | doc_name_idx)]

    logging.debug(f"use_sql: column_idx={column_idx}")
    logging.debug(f"use_sql: field_map={field_map}")

    # Helper function to map column names to display names
    def map_column_name(col_name):
        if col_name.lower() == "count(star)":
            return "COUNT(*)"

        # First, try to extract AS alias from any expression (aggregate functions, json_extract_string, etc.)
        # Pattern: anything AS alias_name
        as_match = re.search(r'\s+AS\s+([^\s,)]+)', col_name, re.IGNORECASE)
        if as_match:
            alias = as_match.group(1).strip('"\'')

            # Use the alias for display name lookup
            if alias in field_map:
                display = field_map[alias]
                return re.sub(r"(/.*|（[^（）]+）)", "", display)
            # If alias not in field_map, try to match case-insensitively
            for field_key, display_value in field_map.items():
                if field_key.lower() == alias.lower():
                    return re.sub(r"(/.*|（[^（）]+）)", "", display_value)
            # Return alias as-is if no mapping found
            return alias

        # Try direct mapping first (for simple column names)
        if col_name in field_map:
            display = field_map[col_name]
            # Clean up any suffix patterns
            return re.sub(r"(/.*|（[^（）]+）)", "", display)

        # Try case-insensitive match for simple column names
        col_lower = col_name.lower()
        for field_key, display_value in field_map.items():
            if field_key.lower() == col_lower:
                return re.sub(r"(/.*|（[^（）]+）)", "", display_value)

        # For aggregate expressions or complex expressions without AS alias,
        # try to replace field names with display names
        result = col_name
        for field_name, display_name in field_map.items():
            # Replace field_name with display_name in the expression
            result = result.replace(field_name, display_name)

        # Clean up any suffix patterns
        result = re.sub(r"(/.*|（[^（）]+）)", "", result)
        return result

    # compose Markdown table
    columns = (
            "|" + "|".join(
        [map_column_name(tbl["columns"][i]["name"]) for i in column_idx]) + (
                "|Source|" if docid_idx and doc_name_idx else "|")
    )

    line = "|" + "|".join(["------" for _ in range(len(column_idx))]) + ("|------|" if docid_idx and docid_idx else "")

    # Build rows ensuring column names match values - create a dict for each row
    # keyed by column name to handle any SQL column order
    rows = []
    for row_idx, r in enumerate(tbl["rows"]):
        row_dict = {tbl["columns"][i]["name"]: r[i] for i in range(len(tbl["columns"])) if i < len(r)}
        if row_idx == 0:
            logging.debug(f"use_sql: First row data: {row_dict}")
        row_values = []
        for col_idx in column_idx:
            col_name = tbl["columns"][col_idx]["name"]
            value = row_dict.get(col_name, " ")
            row_values.append(remove_redundant_spaces(str(value)).replace("None", " "))
        # Add Source column with citation marker if Source column exists
        if docid_idx and doc_name_idx:
            row_values.append(f" ##{row_idx}$$")
        row_str = "|" + "|".join(row_values) + "|"
        if re.sub(r"[ |]+", "", row_str):
            rows.append(row_str)
    if quota:
        rows = "\n".join(rows)
    else:
        rows = "\n".join(rows)
    rows = re.sub(r"T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+Z)?\|", "|", rows)

    if not docid_idx or not doc_name_idx:
        logging.warning(f"use_sql: SQL missing required doc_id or docnm_kwd field. docid_idx={docid_idx}, doc_name_idx={doc_name_idx}. SQL: {sql}")
        # For aggregate queries (COUNT, SUM, AVG, MAX, MIN, DISTINCT), fetch doc_id, docnm_kwd separately
        # to provide source chunks, but keep the original table format answer
        if is_aggregate_sql(sql):
            # Keep original table format as answer
            answer = "\n".join([columns, line, rows])

            # Now fetch doc_id, docnm_kwd to provide source chunks
            # Extract WHERE clause from the original SQL
            where_match = re.search(r"\bwhere\b(.+?)(?:\bgroup by\b|\border by\b|\blimit\b|$)", sql, re.IGNORECASE)
            if where_match:
                where_clause = where_match.group(1).strip()
                # Build a query to get doc_id and docnm_kwd with the same WHERE clause
                chunks_sql = f"select doc_id, docnm_kwd from {table_name} where {where_clause}"
                # Add LIMIT to avoid fetching too many chunks
                if "limit" not in chunks_sql.lower():
                    chunks_sql += " limit 20"
                logging.debug(f"use_sql: Fetching chunks with SQL: {chunks_sql}")
                try:
                    chunks_tbl = settings.retriever.sql_retrieval(chunks_sql, format="json")
                    if chunks_tbl.get("rows") and len(chunks_tbl["rows"]) > 0:
                        # Build chunks reference - use case-insensitive matching
                        chunks_did_idx = next((i for i, c in enumerate(chunks_tbl["columns"]) if c["name"].lower() == "doc_id"), None)
                        chunks_dn_idx = next((i for i, c in enumerate(chunks_tbl["columns"]) if c["name"].lower() in ["docnm_kwd", "docnm"]), None)
                        if chunks_did_idx is not None and chunks_dn_idx is not None:
                            chunks = [{"doc_id": r[chunks_did_idx], "docnm_kwd": r[chunks_dn_idx]} for r in chunks_tbl["rows"]]
                            # Build doc_aggs
                            doc_aggs = {}
                            for r in chunks_tbl["rows"]:
                                doc_id = r[chunks_did_idx]
                                doc_name = r[chunks_dn_idx]
                                if doc_id not in doc_aggs:
                                    doc_aggs[doc_id] = {"doc_name": doc_name, "count": 0}
                                doc_aggs[doc_id]["count"] += 1
                            doc_aggs_list = [{"doc_id": did, "doc_name": d["doc_name"], "count": d["count"]} for did, d in doc_aggs.items()]
                            logging.debug(f"use_sql: Returning aggregate answer with {len(chunks)} chunks from {len(doc_aggs)} documents")
                            return {"answer": answer, "reference": {"chunks": chunks, "doc_aggs": doc_aggs_list}, "prompt": sys_prompt}
                except Exception as e:
                    logging.warning(f"use_sql: Failed to fetch chunks: {e}")
            # Fallback: return answer without chunks
            return {"answer": answer, "reference": {"chunks": [], "doc_aggs": []}, "prompt": sys_prompt}
        # Fallback to table format for other cases
        return {"answer": "\n".join([columns, line, rows]), "reference": {"chunks": [], "doc_aggs": []}, "prompt": sys_prompt}

    docid_idx = list(docid_idx)[0]
    doc_name_idx = list(doc_name_idx)[0]
    doc_aggs = {}
    for r in tbl["rows"]:
        if r[docid_idx] not in doc_aggs:
            doc_aggs[r[docid_idx]] = {"doc_name": r[doc_name_idx], "count": 0}
        doc_aggs[r[docid_idx]]["count"] += 1

    result = {
        "answer": "\n".join([columns, line, rows]),
        "reference": {
            "chunks": [{"doc_id": r[docid_idx], "docnm_kwd": r[doc_name_idx]} for r in tbl["rows"]],
            "doc_aggs": [{"doc_id": did, "doc_name": d["doc_name"], "count": d["count"]} for did, d in doc_aggs.items()],
        },
        "prompt": sys_prompt,
    }
    logging.debug(f"use_sql: Returning answer with {len(result['reference']['chunks'])} chunks from {len(doc_aggs)} documents")
    return result