def format_results_to_html(run_id):
    results_dir = Path(f"results_{run_id}")
    for f in results_dir.glob("*.jsonl"):
        html_file = f.with_suffix(".html")
        lines = f.read_text().splitlines(keepends=True)
        data = [json.loads(line) for line in lines]
        KEYS = data[0].keys()
        print(KEYS)
        FILTER_KEYS = [
            "gpu",
            "pytorch_version",
            "cuda_version",
            "pytorch_mode",
            "is_golden",
            "data_type",
            "function",
            "pass_type",
            "category",
            "match_full",
            "match_normal",
        ]
        KEY_VALUES = {k: sorted({line[k] for line in data}) for k in FILTER_KEYS}
        with html_file.open("w") as html_f:
            html_f.write("<html><body style='font-family: monospace;'>\n")
            html_f.write(f"<h1>Results for {f.stem}</h1>\n")
            for key, values in KEY_VALUES.items():
                html_f.write(
                    f"<details id='section-{key}'><summary>{key} ({len(values)})</summary>\n"
                )
                html_f.write(
                    f"<a href='#' onclick='document.querySelectorAll(\"#section-{key} input\").forEach(checkbox => checkbox.checked = true);'>Enable all</a>\n"
                )
                html_f.write(
                    f"<a href='#' onclick='document.querySelectorAll(\"#section-{key} input\").forEach(checkbox => checkbox.checked = false);'>Disable all</a>\n"
                )
                for value in values:
                    safe_value = str(value).replace(".", "_")
                    html_f.write(
                        f"<label>\n"
                        f"<input type='checkbox' id='filter-{key}-{safe_value}' checked>"
                        f"{value}</label>\n"
                    )
                    html_f.write(
                        f"<style>body:has(#filter-{key}-{safe_value}:not(:checked)) .visible-{key}-{safe_value} {{ display: none; }}</style>\n"
                    )
                html_f.write("</details>")
            # one more filter: show "first" mode only
            html_f.write("<details><summary>First mode that fails only</summary>\n")
            html_f.write(
                "<label><input type='checkbox' id='filter-mode-first' checked>"
                "Exclude items where a previous mode also fails</label>\n"
            )
            html_f.write("</details>\n")
            # column filter:
            html_f.write(
                "<details id='section-columns'><summary>Column filter</summary>\n"
            )
            html_f.write(
                "<a href='#' onclick='document.querySelectorAll(\"#section-columns input\").forEach(checkbox => checkbox.checked = true);'>Enable all</a>\n"
            )
            html_f.write(
                "<a href='#' onclick='document.querySelectorAll(\"#section-columns input\").forEach(checkbox => checkbox.checked = false);'>Disable all</a>\n"
            )
            DEFAULT_HIDDEN_KEYS = [
                "gpu",
                "pytorch_version",
                "cuda_version",
                "is_golden",
            ]
            for key in KEYS:
                html_f.write(
                    f"<label><input type='checkbox' id='filter-column-{key}' {'' if key in DEFAULT_HIDDEN_KEYS else 'checked'}>{key}</label>\n"
                )
                html_f.write(
                    f"<style>body:has(#filter-column-{key}:not(:checked)) .visible-column-{key} {{ display: none; }}</style>\n"
                )
            html_f.write("</details>\n")
            html_f.write("<table>\n")
            html_f.write("<tr>\n")
            for key in KEYS:
                html_f.write(f"<th class='visible-column-{key}'>{key}</th>\n")

            html_f.write("<th>log</th>\n")
            html_f.write("<th>tlparse</th>\n")
            html_f.write("</tr>\n")
            for line in lines:
                data = json.loads(line)
                classes = [
                    f"visible-{k}-{str(data[k]).replace('.', '_')}" for k in KEY_VALUES
                ]
                html_f.write(f"<tr class='{' '.join(classes)}'>\n")
                for key in KEYS:
                    html_f.write(f"<td class='visible-column-{key}'>\n")
                    if key == "mismatch_sample":
                        html_f.write(
                            f"<input type='checkbox' id='filter-mismatch-sample-{data['identifier']}'>\n"
                        )
                        html_f.write(
                            f"<style>body:has(#filter-mismatch-sample-{data['identifier']}:not(:checked)) .visible-mismatch-sample-{data['identifier']} {{ display: none; }}</style>\n"
                        )
                    else:
                        html_f.write(f"{data[key]}\n")
                    html_f.write("</td>\n")
                html_f.write(
                    f"<td><a href='logs/{data['identifier']}.log'>log</a></td>"
                )
                html_f.write(
                    f"<td><a href='logs/{data['identifier']}.trace/tl_out/index.html'>trace</a></td>\n"
                )
                html_f.write("</tr>\n")
                if data["mismatch_sample"]:
                    html_f.write(
                        f"<tr class='visible-mismatch-sample-{data['identifier']} {' '.join(classes)}'>\n"
                    )
                    html_f.write(f"<td colspan='{len(KEYS) + 2}'><pre>\n")
                    html_f.write("<table>\n")
                    html_f.write("<tr>\n")
                    html_f.write("<th>pos</th>\n")
                    html_f.write("<th>input</th>\n")
                    html_f.write("<th>output</th>\n")
                    html_f.write("<th>golden</th>\n")
                    html_f.write("<th>rel_err</th>\n")
                    html_f.write("</tr>\n")
                    for sample in data["mismatch_sample"]:
                        html_f.write("<tr>\n")
                        html_f.write(f"<td>{sample['pos']}</td>\n")
                        html_f.write(
                            f"<td>{', '.join(map(str, sample['input']))}</td>\n"
                        )
                        html_f.write(f"<td>{sample['output']}</td>\n")
                        html_f.write(f"<td>{sample['golden']}</td>\n")
                        html_f.write(f"<td>{sample['rel_err']}</td>\n")
                        html_f.write("</tr>\n")
                    html_f.write("</table>\n")
                    html_f.write("</td>\n")
                    html_f.write("</tr>\n")

            html_f.write("</table>\n")
            html_f.write("<style>\n")
            # implement the various filters
            html_f.write("</style>\n")
            html_f.write("</body></html>\n")