def query_open_prs(owner: str, repo: str, base_branch: str) -> list[dict]:
    """Query all open PRs targeting the specified base branch."""
    prs = []
    cursor = None

    while True:
        after_clause = f', after: "{cursor}"' if cursor else ""
        query = f'''
        query {{
            repository(owner: "{owner}", name: "{repo}") {{
                pullRequests(
                    first: 100{after_clause},
                    states: OPEN,
                    baseRefName: "{base_branch}",
                    orderBy: {{field: UPDATED_AT, direction: DESC}}
                ) {{
                    totalCount
                    edges {{
                        node {{
                            number
                            title
                            url
                            updatedAt
                            author {{ login }}
                            headRefName
                            baseRefName
                            files(first: 100) {{
                                nodes {{ path }}
                                pageInfo {{ hasNextPage }}
                            }}
                        }}
                    }}
                    pageInfo {{
                        endCursor
                        hasNextPage
                    }}
                }}
            }}
        }}
        '''

        result = run_gh(["api", "graphql", "-f", f"query={query}"])
        data = json.loads(result.stdout)

        if "errors" in data:
            print(f"GraphQL errors: {data['errors']}", file=sys.stderr)
            sys.exit(1)

        pr_data = data["data"]["repository"]["pullRequests"]
        for edge in pr_data["edges"]:
            node = edge["node"]
            files_data = node["files"]
            # Warn if PR has more than 100 files (API limit, we only fetch first 100)
            if files_data.get("pageInfo", {}).get("hasNextPage"):
                print(f"Warning: PR #{node['number']} has >100 files, overlap detection may be incomplete", file=sys.stderr)
            prs.append({
                "number": node["number"],
                "title": node["title"],
                "url": node["url"],
                "updated_at": node.get("updatedAt"),
                "author": node["author"]["login"] if node["author"] else "unknown",
                "head_ref": node["headRefName"],
                "base_ref": node["baseRefName"],
                "files": [f["path"] for f in files_data["nodes"]]
            })

        if not pr_data["pageInfo"]["hasNextPage"]:
            break
        cursor = pr_data["pageInfo"]["endCursor"]

    return prs