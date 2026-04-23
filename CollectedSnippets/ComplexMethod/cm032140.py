async def example_usage():
    """GitHubSource使用示例"""
    # 创建客户端实例（可选传入API令牌）
    # github = GitHubSource(api_key="your_github_token")
    github = GitHubSource()

    try:
        # 示例1：搜索热门Python仓库
        print("\n=== 示例1：搜索热门Python仓库 ===")
        repos = await github.search_repositories(
            query="language:python stars:>1000",
            sort="stars",
            order="desc",
            per_page=5
        )

        if repos and "items" in repos:
            for i, repo in enumerate(repos["items"], 1):
                print(f"\n--- 仓库 {i} ---")
                print(f"名称: {repo['full_name']}")
                print(f"描述: {repo['description']}")
                print(f"星标数: {repo['stargazers_count']}")
                print(f"Fork数: {repo['forks_count']}")
                print(f"最近更新: {repo['updated_at']}")
                print(f"URL: {repo['html_url']}")

        # 示例2：获取特定仓库的详情
        print("\n=== 示例2：获取特定仓库的详情 ===")
        repo_details = await github.get_repo("microsoft", "vscode")
        if repo_details:
            print(f"名称: {repo_details['full_name']}")
            print(f"描述: {repo_details['description']}")
            print(f"星标数: {repo_details['stargazers_count']}")
            print(f"Fork数: {repo_details['forks_count']}")
            print(f"默认分支: {repo_details['default_branch']}")
            print(f"开源许可: {repo_details.get('license', {}).get('name', '无')}")
            print(f"语言: {repo_details['language']}")
            print(f"Open Issues数: {repo_details['open_issues_count']}")

        # 示例3：获取仓库的提交历史
        print("\n=== 示例3：获取仓库的最近提交 ===")
        commits = await github.get_repo_commits("tensorflow", "tensorflow", per_page=5)
        if commits:
            for i, commit in enumerate(commits, 1):
                print(f"\n--- 提交 {i} ---")
                print(f"SHA: {commit['sha'][:7]}")
                print(f"作者: {commit['commit']['author']['name']}")
                print(f"日期: {commit['commit']['author']['date']}")
                print(f"消息: {commit['commit']['message'].splitlines()[0]}")

        # 示例4：搜索代码
        print("\n=== 示例4：搜索代码 ===")
        code_results = await github.search_code(
            query="filename:README.md language:markdown pytorch in:file",
            per_page=3
        )
        if code_results and "items" in code_results:
            print(f"共找到: {code_results['total_count']} 个结果")
            for i, item in enumerate(code_results["items"], 1):
                print(f"\n--- 代码 {i} ---")
                print(f"仓库: {item['repository']['full_name']}")
                print(f"文件: {item['path']}")
                print(f"URL: {item['html_url']}")

        # 示例5：获取文件内容
        print("\n=== 示例5：获取文件内容 ===")
        file_content = await github.get_file_content("python", "cpython", "README.rst")
        if file_content and "decoded_content" in file_content:
            content = file_content["decoded_content"]
            print(f"文件名: {file_content['name']}")
            print(f"大小: {file_content['size']} 字节")
            print(f"内容预览: {content[:200]}...")

        # 示例6：获取仓库使用的编程语言
        print("\n=== 示例6：获取仓库使用的编程语言 ===")
        languages = await github.get_repository_languages("facebook", "react")
        if languages:
            print(f"React仓库使用的编程语言:")
            for lang, bytes_of_code in languages.items():
                print(f"- {lang}: {bytes_of_code} 字节")

        # 示例7：获取组织信息
        print("\n=== 示例7：获取组织信息 ===")
        org_info = await github.get_organization("google")
        if org_info:
            print(f"名称: {org_info['name']}")
            print(f"描述: {org_info.get('description', '无')}")
            print(f"位置: {org_info.get('location', '未指定')}")
            print(f"公共仓库数: {org_info['public_repos']}")
            print(f"成员数: {org_info.get('public_members', 0)}")
            print(f"URL: {org_info['html_url']}")

        # 示例8：获取用户信息
        print("\n=== 示例8：获取用户信息 ===")
        user_info = await github.get_user("torvalds")
        if user_info:
            print(f"名称: {user_info['name']}")
            print(f"公司: {user_info.get('company', '无')}")
            print(f"博客: {user_info.get('blog', '无')}")
            print(f"位置: {user_info.get('location', '未指定')}")
            print(f"公共仓库数: {user_info['public_repos']}")
            print(f"关注者数: {user_info['followers']}")
            print(f"URL: {user_info['html_url']}")

    except Exception as e:
        print(f"发生错误: {str(e)}")
        import traceback
        print(traceback.format_exc())