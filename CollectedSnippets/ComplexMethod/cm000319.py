def post_or_update_comment(pr_number: int, body: str):
    """Post a new comment or update existing overlap detection comment."""
    if not body:
        return

    marker = "## 🔍 PR Overlap Detection"

    # Find existing comment using GraphQL
    owner, repo = get_repo_info()
    query = f'''
    query {{
        repository(owner: "{owner}", name: "{repo}") {{
            pullRequest(number: {pr_number}) {{
                comments(first: 100) {{
                    nodes {{
                        id
                        body
                        author {{ login }}
                    }}
                }}
            }}
        }}
    }}
    '''

    result = run_gh(["api", "graphql", "-f", f"query={query}"], check=False)

    existing_comment_id = None
    if result.returncode == 0:
        try:
            data = json.loads(result.stdout)
            comments = data.get("data", {}).get("repository", {}).get("pullRequest", {}).get("comments", {}).get("nodes", [])
            for comment in comments:
                if marker in comment.get("body", ""):
                    existing_comment_id = comment["id"]
                    break
        except Exception as e:
            print(f"Warning: Could not search for existing comment: {e}", file=sys.stderr)

    if existing_comment_id:
        # Update existing comment using GraphQL mutation
        # Use json.dumps for proper escaping of all special characters
        escaped_body = json.dumps(body)[1:-1]  # Strip outer quotes added by json.dumps
        mutation = f'''
        mutation {{
            updateIssueComment(input: {{id: "{existing_comment_id}", body: "{escaped_body}"}}) {{
                issueComment {{ id }}
            }}
        }}
        '''
        result = run_gh(["api", "graphql", "-f", f"query={mutation}"], check=False)
        if result.returncode == 0:
            print(f"Updated existing overlap comment")
        else:
            # Fallback to posting new comment
            print(f"Failed to update comment, posting new one: {result.stderr}", file=sys.stderr)
            run_gh(["pr", "comment", str(pr_number), "--body", body])
    else:
        # Post new comment
        run_gh(["pr", "comment", str(pr_number), "--body", body])