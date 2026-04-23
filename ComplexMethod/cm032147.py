async def get_latest_papers(
        self,
        category: str,
        debug: bool = False,
        batch_size: int = 50
    ) -> List[PaperMetadata]:
        """获取指定类别的最新论文

        通过 RSS feed 获取最新发布的论文，然后批量获取详细信息

        Args:
            category: arXiv类别，例如：
                     - 整个领域: 'cs'
                     - 具体方向: 'cs.AI'
                     - 多个类别: 'cs.AI+q-bio.NC'
            debug: 是否为调试模式，如果为True则只返回5篇最新论文
            batch_size: 批量获取论文的数量，默认50

        Returns:
            论文列表

        Raises:
            ValueError: 如果类别无效
        """
        try:
            # 处理类别格式
            # 1. 转换为小写
            # 2. 确保多个类别之间使用+连接
            category = category.lower().replace(' ', '+')

            # 构建RSS feed URL
            feed_url = f"https://rss.arxiv.org/rss/{category}"
            print(f"正在获取RSS feed: {feed_url}")  # 添加调试信息

            feed = feedparser.parse(feed_url)

            # 检查feed是否有效
            if hasattr(feed, 'status') and feed.status != 200:
                raise ValueError(f"获取RSS feed失败，状态码: {feed.status}")

            if not feed.entries:
                print(f"警告：未在feed中找到任何条目")  # 添加调试信息
                print(f"Feed标题: {feed.feed.title if hasattr(feed, 'feed') else '无标题'}")
                raise ValueError(f"无效的arXiv类别或未找到论文: {category}")

            if debug:
                # 调试模式：只获取5篇最新论文
                search = arxiv.Search(
                    query=f'cat:{category}',
                    sort_by=arxiv.SortCriterion.SubmittedDate,
                    sort_order=arxiv.SortOrder.Descending,
                    max_results=5
                )
                results = list(self.client.results(search))
                return [self._parse_paper_data(result) for result in results]

            # 正常模式：获取所有新论文
            # 从RSS条目中提取arXiv ID
            paper_ids = []
            for entry in feed.entries:
                try:
                    # RSS链接格式可能是以下几种：
                    # - http://arxiv.org/abs/2403.xxxxx
                    # - http://arxiv.org/pdf/2403.xxxxx
                    # - https://arxiv.org/abs/2403.xxxxx
                    link = entry.link or entry.id
                    arxiv_id = link.split('/')[-1].replace('.pdf', '')
                    if arxiv_id:
                        paper_ids.append(arxiv_id)
                except Exception as e:
                    print(f"警告：处理条目时出错: {str(e)}")  # 添加调试信息
                    continue

            if not paper_ids:
                print("未能从feed中提取到任何论文ID")  # 添加调试信息
                return []

            print(f"成功提取到 {len(paper_ids)} 个论文ID")  # 添加调试信息

            # 批量获取论文详情
            papers = []
            with tqdm(total=len(paper_ids), desc="获取arXiv论文") as pbar:
                for i in range(0, len(paper_ids), batch_size):
                    batch_ids = paper_ids[i:i + batch_size]
                    search = arxiv.Search(
                        id_list=batch_ids,
                        max_results=len(batch_ids)
                    )
                    batch_results = list(self.client.results(search))
                    papers.extend([self._parse_paper_data(result) for result in batch_results])
                    pbar.update(len(batch_results))

            return papers

        except Exception as e:
            print(f"获取最新论文时发生错误: {str(e)}")
            import traceback
            print(traceback.format_exc())  # 添加完整的错误追踪
            return []