def create_readable_report(
    coverage_collection: dict, additional_tested_collection: dict, output_dir: str
) -> None:
    """
    Helper function to create a very simple HTML view out of the collected metrics.
    The file will be named "report_metric_coverage.html"

    :params coverage_collection: the dict with the coverage collection
    :params additional_tested_collection: dict with coverage of APIs only for acceptance tests
    :params output_dir: the directory where the outcoming html file should be stored to.
    """
    service_overview_coverage = """
    <table>
      <tr>
        <th style="text-align: left">Service</th>
        <th style="text-align: right">Coverage of Acceptance Tests Suite</th>
      </tr>
    """
    coverage_details = """
    <table>
      <tr>
        <th style="text-align: left">Service</th>
        <th style="text-align: left">Operation</th>
        <th>Return Code</th>
        <th>Covered By Acceptance Test</th>
      </tr>"""
    additional_test_details = ""
    coverage_collection = sort_dict_helper(coverage_collection)
    additional_tested_collection = sort_dict_helper(additional_tested_collection)
    for service, operations in coverage_collection.items():
        # count tested operations vs operations that are somehow covered with acceptance
        amount_ops = len(operations)
        covered_ops = len([op for op, details in operations.items() if any(details.values())])
        percentage_covered = 100 * covered_ops / amount_ops
        service_overview_coverage += "    <tr>\n"
        service_overview_coverage += f"    <td>{service}</td>\n"
        service_overview_coverage += (
            f"""    <td style="text-align: right">{percentage_covered:.2f}%</td>\n"""
        )
        service_overview_coverage += "    </tr>\n"

        for op_name, details in operations.items():
            for response_code, covered in details.items():
                coverage_details += "    <tr>\n"
                coverage_details += f"    <td>{service}</td>\n"
                coverage_details += f"    <td>{op_name}</td>\n"
                coverage_details += f"""    <td style="text-align: center">{response_code}</td>\n"""
                coverage_details += (
                    f"""    <td style="text-align: center">{"✅" if covered else "❌"}</td>\n"""
                )
                coverage_details += "    </tr>\n"
    if additional_tested_collection:
        additional_test_details = """<table>
      <tr>
        <th>Service</th>
        <th>Operation</th>
        <th>Return Code</th>
        <th>Covered By Acceptance Test</th>
      </tr>"""
        for service, operations in additional_tested_collection.items():
            for op_name, details in operations.items():
                for response_code, covered in details.items():
                    additional_test_details += "    <tr>\n"
                    additional_test_details += f"    <td>{service}</td>\n"
                    additional_test_details += f"    <td>{op_name}</td>\n"
                    additional_test_details += f"    <td>{response_code}</td>\n"
                    additional_test_details += f"    <td>{'✅' if covered else '❌'}</td>\n"
                    additional_test_details += "    </tr>\n"
        additional_test_details += "</table><br/>\n"
    service_overview_coverage += "</table><br/>\n"
    coverage_details += "</table><br/>\n"
    path = Path(output_dir)
    file_name = path.joinpath("report_metric_coverage.html")
    with open(file_name, "w") as fd:
        fd.write(
            """<!doctype html>
<html>
  <style>
    h1 {text-align: center;}
    h2 {text-align: center;}
    table {text-align: left;margin-left:auto;margin-right:auto;}
    p {text-align: center;}
    div {text-align: center;}
 </style>
<body>"""
        )
        fd.write("  <h1>Diff Report Metrics Coverage</h1>\n")
        fd.write("   <h2>Service Coverage</h2>\n")
        fd.write(
            "       <div><p>Assumption: the initial test suite is considered to have 100% coverage.</p>\n"
        )
        fd.write(f"<p>{service_overview_coverage}</p></div>\n")
        fd.write("   <h2>Coverage Details</h2>\n")
        fd.write(f"<div>{coverage_details}</div>")
        if additional_test_details:
            fd.write("    <h2>Additional Test Coverage</h2>\n")
            fd.write(
                "<div>     Note: this is probably wrong usage of the script. It includes operations that have been covered with the acceptance tests only"
            )
            fd.write(f"<p>{additional_test_details}</p></div>\n")
        fd.write("</body></html>")