def test_print_prompt_summary_long_content():
    messages = [
        {"role": "system", "content": "This is a very long system message that should be wrapped properly within the box boundaries"},
        {"role": "user", "content": "short"},
    ]

    # Capture stdout
    captured_output = io.StringIO()
    sys.stdout = captured_output

    print_prompt_summary(cast(list[ChatCompletionMessageParam], messages))

    # Reset stdout
    sys.stdout = sys.__stdout__

    output = captured_output.getvalue()
    lines = output.strip().split('\n')

    # Check that all lines have consistent box formatting
    for line in lines:
        if line.startswith('│') and line.endswith('│'):
            # All content lines should have same length
            assert len(line) == len(lines[0]) if lines[0].startswith('┌') else True

    # Check content is present
    assert "PROMPT SUMMARY" in output
    assert "SYSTEM:" in output
    assert "USER: short" in output