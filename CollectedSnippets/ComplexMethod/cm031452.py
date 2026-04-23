def _complete(con, text, state):
    global _completion_matches

    if state == 0:
        if text.startswith("."):
            _completion_matches = [
                c + " " for c in CLI_COMMANDS if c.startswith(text)
            ]
        else:
            text_upper = text.upper()
            _completion_matches = [
                c + " " for c in SQLITE_KEYWORDS if c.startswith(text_upper)
            ]

            cursor = con.cursor()
            schemata = tuple(row[1] for row
                             in cursor.execute("PRAGMA database_list"))
            # tables, indexes, triggers, and views
            # escape '_' which can appear in attached database names
            select_clauses = (
                f"""\
                SELECT name || ' ' FROM \"{schema}\".sqlite_master
                WHERE name LIKE REPLACE(:text, '_', '^_') || '%' ESCAPE '^'"""
                for schema in schemata
            )
            _completion_matches.extend(
                row[0]
                for row in cursor.execute(
                    " UNION ".join(select_clauses), {"text": text}
                )
            )
            # columns
            try:
                select_clauses = (
                    f"""\
                    SELECT pti.name || ' ' FROM "{schema}".sqlite_master AS sm
                    JOIN pragma_table_xinfo(sm.name,'{schema}') AS pti
                    WHERE sm.type='table' AND
                    pti.name LIKE REPLACE(:text, '_', '^_') || '%' ESCAPE '^'"""
                    for schema in schemata
                )
                _completion_matches.extend(
                    row[0]
                    for row in cursor.execute(
                        " UNION ".join(select_clauses), {"text": text}
                    )
                )
            except OperationalError:
                # skip on SQLite<3.16.0 where pragma table-valued function is
                # not supported yet
                pass
            # functions
            try:
                _completion_matches.extend(
                    row[0] for row in cursor.execute("""\
                    SELECT DISTINCT UPPER(name) || '('
                    FROM pragma_function_list()
                    WHERE name NOT IN ('->', '->>') AND
                    name LIKE REPLACE(:text, '_', '^_') || '%' ESCAPE '^'""",
                    {"text": text},
                    )
                )
            except OperationalError:
                # skip on SQLite<3.30.0 where function_list is not supported yet
                pass
            # schemata
            text_lower = text.lower()
            _completion_matches.extend(c for c in schemata
                                       if c.lower().startswith(text_lower))
            _completion_matches = sorted(set(_completion_matches))
    try:
        return _completion_matches[state]
    except IndexError:
        return None