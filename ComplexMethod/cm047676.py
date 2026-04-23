def __iter__(self):
        for entry in self.pofile:
            if entry.obsolete:
                continue

            # in case of moduleS keep only the first
            match = re.match(r"(module[s]?): (\w+)", entry.comment)
            _, module = match.groups()
            comments = "\n".join([c for c in entry.comment.split('\n') if not c.startswith('module:')])
            source = entry.msgid
            translation = entry.msgstr
            found_code_occurrence = False
            for occurrence, line_number in entry.occurrences:
                match = re.match(r'(model|model_terms):([\w.]+),([\w]+):(\w+)\.([^ ]+)', occurrence)
                if match:
                    type, model_name, field_name, module, xmlid = match.groups()
                    yield {
                        'type': type,
                        'imd_model': model_name,
                        'name': model_name+','+field_name,
                        'imd_name': xmlid,
                        'res_id': None,
                        'src': source,
                        'value': translation,
                        'comments': comments,
                        'module': module,
                    }
                    continue

                match = re.match(r'(code):([\w/.]+)', occurrence)
                if match:
                    type, name = match.groups()
                    if found_code_occurrence:
                        # unicity constrain on code translation
                        continue
                    found_code_occurrence = True
                    yield {
                        'type': type,
                        'name': name,
                        'src': source,
                        'value': translation,
                        'comments': comments,
                        'res_id': int(line_number),
                        'module': module,
                    }
                    continue

                match = re.match(r'(selection):([\w.]+),([\w]+)', occurrence)
                if match:
                    _logger.info("Skipped deprecated occurrence %s", occurrence)
                    continue

                match = re.match(r'(sql_constraint|constraint):([\w.]+)', occurrence)
                if match:
                    _logger.info("Skipped deprecated occurrence %s", occurrence)
                    continue
                _logger.error("malformed po file: unknown occurrence: %s", occurrence)