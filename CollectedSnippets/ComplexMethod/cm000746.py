async def resolve_discussion(
        credentials: GithubCredentials,
        repo: str,
        pr_number: int,
        comment_id: int,
        resolve: bool,
    ) -> bool:
        api = get_api(credentials, convert_urls=False)

        # Extract owner and repo name
        parts = repo.split("/")
        owner = parts[0]
        repo_name = parts[1]

        # GitHub GraphQL API is needed for resolving/unresolving discussions
        # First, we need to get the node ID of the comment
        graphql_url = "https://api.github.com/graphql"

        # Query to get the review comment node ID
        query = """
        query($owner: String!, $repo: String!, $number: Int!) {
          repository(owner: $owner, name: $repo) {
            pullRequest(number: $number) {
              reviewThreads(first: 100) {
                nodes {
                  comments(first: 100) {
                    nodes {
                      databaseId
                      id
                    }
                  }
                  id
                  isResolved
                }
              }
            }
          }
        }
        """

        variables = {"owner": owner, "repo": repo_name, "number": pr_number}

        response = await api.post(
            graphql_url, json={"query": query, "variables": variables}
        )
        data = response.json()

        # Find the thread containing our comment
        thread_id = None
        for thread in data["data"]["repository"]["pullRequest"]["reviewThreads"][
            "nodes"
        ]:
            for comment in thread["comments"]["nodes"]:
                if comment["databaseId"] == comment_id:
                    thread_id = thread["id"]
                    break
            if thread_id:
                break

        if not thread_id:
            raise ValueError(f"Comment {comment_id} not found in pull request")

        # Now resolve or unresolve the thread
        # GitHub's GraphQL API has separate mutations for resolve and unresolve
        if resolve:
            mutation = """
            mutation($threadId: ID!) {
              resolveReviewThread(input: {threadId: $threadId}) {
                thread {
                  isResolved
                }
              }
            }
            """
        else:
            mutation = """
            mutation($threadId: ID!) {
              unresolveReviewThread(input: {threadId: $threadId}) {
                thread {
                  isResolved
                }
              }
            }
            """

        mutation_variables = {"threadId": thread_id}

        response = await api.post(
            graphql_url, json={"query": mutation, "variables": mutation_variables}
        )
        result = response.json()

        if "errors" in result:
            raise Exception(f"GraphQL error: {result['errors']}")

        return True