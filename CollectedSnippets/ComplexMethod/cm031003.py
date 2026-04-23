def _run_suite(suite):
    """Run tests from a unittest.TestSuite-derived class."""
    runner = get_test_runner(sys.stdout,
                             verbosity=support.verbose,
                             capture_output=(support.junit_xml_list is not None))

    result = runner.run(suite)

    if support.junit_xml_list is not None:
        import xml.etree.ElementTree as ET
        xml_elem = result.get_xml_element()
        xml_str = ET.tostring(xml_elem).decode('ascii')
        support.junit_xml_list.append(xml_str)

    if not result.testsRun and not result.skipped and not result.errors:
        raise support.TestDidNotRun
    if not result.wasSuccessful():
        stats = TestStats.from_unittest(result)
        if len(result.errors) == 1 and not result.failures:
            err = result.errors[0][1]
        elif len(result.failures) == 1 and not result.errors:
            err = result.failures[0][1]
        else:
            err = "multiple errors occurred"
            if not support.verbose: err += "; run in verbose mode for details"
        errors = [(str(tc), exc_str) for tc, exc_str in result.errors]
        failures = [(str(tc), exc_str) for tc, exc_str in result.failures]
        raise support.TestFailedWithDetails(err, errors, failures, stats=stats)
    return result