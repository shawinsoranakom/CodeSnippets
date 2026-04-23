def try_report(cr, uid, rname, ids, data=None, context=None, our_module=None, report_type=None):
    """ Try to render a report <rname> with contents of ids

        This function should also check for common pitfalls of reports.
    """
    if context is None:
        context = {}
    _test_logger.info("  - Trying %s.create(%r)", rname, ids)

    env = api.Environment(cr, uid, context)

    res_data, res_format = env['ir.actions.report']._render(rname, ids, data=data)

    if not res_data:
        raise ValueError("Report %s produced an empty result!" % rname)

    _logger.debug("Have a %s report for %s, will examine it", res_format, rname)
    if res_format == 'pdf':
        if res_data[:5] != b'%PDF-':
            raise ValueError("Report %s produced a non-pdf header, %r" % (rname, res_data[:10]))
        res_text = None
        try:
            fd, rfname = tempfile.mkstemp(suffix=res_format)
            os.write(fd, res_data)
            os.close(fd)

            proc = Popen(['pdftotext', '-enc', 'UTF-8', '-nopgbrk', rfname, '-'], shell=False, stdout=PIPE, encoding="utf-8")
            res_text, _stderr = proc.communicate()
            os.unlink(rfname)
        except Exception:
            _logger.debug("Unable to parse PDF report: install pdftotext to perform automated tests.")

        if res_text:
            for line in res_text.splitlines():
                if ('[[' in line) or ('[ [' in line):
                    _logger.error("Report %s may have bad expression near: \"%s\".", rname, line[80:])
            # TODO more checks, what else can be a sign of a faulty report?
    elif res_format == 'html':
        pass
    else:
        _logger.warning("Report %s produced a \"%s\" chunk, cannot examine it", rname, res_format)
        return False

    _test_logger.info("  + Report %s produced correctly.", rname)
    return True