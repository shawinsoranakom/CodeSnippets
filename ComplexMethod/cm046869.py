def __combined_prompt_processor__(examples):
        if len(examples) == 0:
            return {user_column_name: []}

        first_key = next(iter(examples.keys()), None)
        if first_key is None:
            return {user_column_name: []}
        n_rows = len(examples[first_key])

        texts = []
        for row_idx in range(n_rows):
            row_values = {column: examples[column][row_idx] for column in columns}
            formatter_values = {}

            for formatter_template in formatter_templates:
                if formatter_template[0] == "required":
                    _, _, needed_columns = formatter_template
                    for column in needed_columns:
                        formatter_values[column] = row_values[column]
                    continue

                _, optional_name, prompt, needed_columns = formatter_template
                if row_values[needed_columns[0]] not in (None, ""):
                    prompt_values = {column: row_values[column] for column in needed_columns}
                    formatter_values[optional_name] = prompt.format(**prompt_values)
                else:
                    formatter_values[optional_name] = ""

            texts.append(merged_prompt.format(**formatter_values))

        return {user_column_name: texts}