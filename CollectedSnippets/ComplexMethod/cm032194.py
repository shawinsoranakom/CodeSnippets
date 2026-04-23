async def _get_code_details(self, code_results: List[Dict]) -> List[Dict]:
        """获取代码详情"""
        enhanced_results = []

        for item in code_results:
            try:
                repo = item.get('repository', {})
                file_path = item.get('path', '')
                repo_name = repo.get('full_name', '')

                if repo_name and file_path:
                    owner, repo_name = repo_name.split('/')

                    # 获取文件内容
                    file_content = await self.github.get_file_content(owner, repo_name, file_path)
                    if file_content and "decoded_content" in file_content:
                        item['code_content'] = file_content["decoded_content"]

                        # 获取仓库基本信息
                        repo_details = await self.github.get_repo(owner, repo_name)
                        if repo_details:
                            item['repository'] = repo_details

                enhanced_results.append(item)
            except Exception as e:
                print(f"获取代码详情时出错: {str(e)}")
                enhanced_results.append(item)  # 添加原始信息

        return enhanced_results