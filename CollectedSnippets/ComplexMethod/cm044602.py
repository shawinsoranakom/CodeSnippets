def test_highlight_regex_callable():
    text = Text("Vulnerability CVE-2018-6543 detected")
    re_cve = r"CVE-\d{4}-\d+"
    compiled_re_cve = re.compile(r"CVE-\d{4}-\d+")

    def get_style(text: str) -> Style:
        return Style.parse(
            f"bold yellow link https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword={text}"
        )

    # string
    count = text.highlight_regex(re_cve, get_style)
    assert count == 1
    assert len(text._spans) == 1
    assert text._spans[0].start == 14
    assert text._spans[0].end == 27
    assert (
        text._spans[0].style.link
        == "https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword=CVE-2018-6543"
    )

    # Clear the tracked _spans for the regular expression object's use
    text._spans.clear()

    # regular expression object
    count = text.highlight_regex(compiled_re_cve, get_style)
    assert count == 1
    assert len(text._spans) == 1
    assert text._spans[0].start == 14
    assert text._spans[0].end == 27
    assert (
        text._spans[0].style.link
        == "https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword=CVE-2018-6543"
    )