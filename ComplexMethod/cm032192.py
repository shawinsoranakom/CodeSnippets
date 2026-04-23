async def _get_repo_details(self, repos: List[Dict]) -> List[Dict]:
        """获取仓库详细信息"""
        enhanced_repos = []

        for repo in repos:
            try:
                # 获取README信息
                owner = repo.get('owner', {}).get('login') if repo.get('owner') is not None else None
                repo_name = repo.get('name')

                if owner and repo_name:
                    readme = await self.github.get_repo_readme(owner, repo_name)
                    if readme and "decoded_content" in readme:
                        # 提取README的前1000个字符作为摘要
                        repo['readme_excerpt'] = readme["decoded_content"][:1000] + "..."

                    # 获取语言使用情况
                    languages = await self.github.get_repository_languages(owner, repo_name)
                    if languages:
                        repo['languages_detail'] = languages

                    # 获取最新发布版本
                    releases = await self.github.get_repo_releases(owner, repo_name, per_page=1)
                    if releases and len(releases) > 0:
                        repo['latest_release'] = releases[0]

                    # 获取主题标签
                    topics = await self.github.get_repo_topics(owner, repo_name)
                    if topics and "names" in topics:
                        repo['topics'] = topics["names"]

                enhanced_repos.append(repo)
            except Exception as e:
                print(f"获取仓库 {repo.get('full_name')} 详情时出错: {str(e)}")
                enhanced_repos.append(repo)  # 添加原始仓库信息

        return enhanced_repos