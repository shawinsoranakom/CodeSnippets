def main():
    try:
        github = Github(GITHUB_TOKEN)
        pull = get_pr_details(github)
        if not pull:
            print(f"No PR number found")
            exit()
        diff = get_diff(pull.diff_url)
    except Exception as e:
        print(f"Error get details: {e.__class__.__name__}: {e}")
        exit(1)
    try:
        review = get_ai_response(create_review_prompt(pull, diff), False)
    except Exception as e:
        print(f"Error create review: {e}")
        exit(1)
    if pull.get_reviews().totalCount > 0 or pull.get_issue_comments().totalCount > 0:
        pull.create_issue_comment(body=review)
        return
    try:
        comments = analyze_code(pull, diff)
    except Exception as e:
        print(f"Error analyze: {e}")
        exit(1)
    print("Comments:", comments)
    try:
        if comments:
            pull.create_review(body=review, comments=comments)
        else:
            pull.create_issue_comment(body=review)
    except Exception as e:
        print(f"Error posting review: {e}")
        exit(1)