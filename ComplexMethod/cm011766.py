def visualize_results(
    n: int, results: ResultType, filename: str = "results.html"
) -> None:
    """
    Creates an HTML document representing the results of running the fuzzer with fuzz_n_tuple, with n = 2.
    """
    # TODO support more dimensions
    assert n == 2
    assert len(results) > 0

    input_set: OrderedSet[str] = OrderedSet({})
    for key in results.keys():  # noqa: SIM118
        input_set.add(key[0])
        input_set.add(key[1])
    input_list = sorted(input_set)

    # Start the HTML content
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title> Fuzzer Visualization</title>
        <style>
            table {
                border-collapse: collapse;
                width: 50%;
                margin: 20px auto;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: center;
            }
            th {
                background-color: #f2f2f2;
            }
            .skipped {
                background-color: yellow;
            }
            .passed {
                background-color: green;
                color: white;
            }
            .failed {
                background-color: red;
                color: white;
            }
        </style>
    </head>
    <body>
        <h2 style="text-align: center;">Fuzzer Visualization</h2>
        <table>
        <thead>
    """

    html_content += "<tr><th>\\</th>"
    for col_name in input_list:
        col = "<br>".join(col_name)
        html_content += f"<th>{col}</th>"
    html_content += "</tr></thead><tbody>"

    # Add table rows
    for row_name in input_list:
        html_content += f"<tr><th>{row_name}</th>"
        for col_name in input_list:
            # Determine the status class for the cell
            status_enum = results.lookup((row_name, col_name))
            status_class = ""
            status_val = ""
            if status_enum == Status.SKIPPED:
                status_class = "skipped"
                status_val = "-"
            elif status_enum == Status.PASSED:
                status_class = "passed"
                status_val = "O"
            elif status_enum == Status.FAILED_RUN_EAGER_EXCEPTION:
                status_class = "failed"
                status_val = "e"
            elif status_enum == Status.FAILED_RUN_COMPILE_EXCEPTION:
                status_class = "failed"
                status_val = "E"
            elif status_enum == Status.FAILED_RUN_RETURN:
                status_class = "failed"
                status_val = "R"
            elif status_enum == Status.FAILED_COMPILE:
                status_class = "failed"
                status_val = "C"
            else:
                status_class = "skipped"
                status_val = "-"

            html_content += f'<td class="{status_class}">{status_val}</td>'
        html_content += "</tr>"

    html_content += """
        </tbody>
        </table>
    </body>
    </html>
    """

    with open(filename, "w") as file:
        file.write(html_content)