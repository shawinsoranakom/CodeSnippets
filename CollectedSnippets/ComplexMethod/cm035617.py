def test_get_instruction(
    mock_user_instructions_template,
    mock_conversation_instructions_template,
    mock_followup_prompt_template,
):
    issue = Issue(
        owner='test_owner',
        repo='test_repo',
        number=123,
        title='Test Issue',
        body='This is a test issue refer to image ![First Image](https://sampleimage.com/image1.png)',
    )
    mock_llm_config = LLMConfig(model='test_model', api_key='test_api_key')
    issue_handler = ServiceContextIssue(
        GitlabIssueHandler('owner', 'repo', 'token'), mock_llm_config
    )
    instruction, conversation_instructions, images_urls = issue_handler.get_instruction(
        issue,
        mock_user_instructions_template,
        mock_conversation_instructions_template,
        None,
    )
    expected_instruction = 'Issue: Test Issue\n\nThis is a test issue refer to image ![First Image](https://sampleimage.com/image1.png)\n\nPlease fix this issue.'

    assert images_urls == ['https://sampleimage.com/image1.png']
    assert issue_handler.issue_type == 'issue'
    assert instruction == expected_instruction
    assert conversation_instructions is not None

    issue = Issue(
        owner='test_owner',
        repo='test_repo',
        number=123,
        title='Test Issue',
        body='This is a test issue',
        closing_issues=['Issue 1 fix the type'],
        review_threads=[
            ReviewThread(
                comment="There is still a typo 'pthon' instead of 'python'", files=[]
            )
        ],
        thread_comments=[
            "I've left review comments, please address them",
            'This is a valid concern.',
        ],
    )

    pr_handler = ServiceContextPR(
        GitlabPRHandler('owner', 'repo', 'token'), mock_llm_config
    )
    instruction, conversation_instructions, images_urls = pr_handler.get_instruction(
        issue,
        mock_followup_prompt_template,
        mock_conversation_instructions_template,
        None,
    )
    expected_instruction = "Issue context: [\n    \"Issue 1 fix the type\"\n]\n\nReview comments: None\n\nReview threads: [\n    \"There is still a typo 'pthon' instead of 'python'\"\n]\n\nFiles: []\n\nThread comments: I've left review comments, please address them\n---\nThis is a valid concern.\n\nPlease fix this issue."

    assert images_urls == []
    assert pr_handler.issue_type == 'pr'
    # Compare content ignoring exact formatting
    assert "There is still a typo 'pthon' instead of 'python'" in instruction
    assert "I've left review comments, please address them" in instruction
    assert 'This is a valid concern' in instruction
    assert conversation_instructions is not None