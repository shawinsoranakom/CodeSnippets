async def get_pr_review_threads(
        self,
        repository: str,
        pr_number: int,
        max_threads: int = 10,
    ) -> list[ReviewThread]:
        owner, repo = self._split_repo(repository)
        url = self._build_repo_api_url(owner, repo, 'pulls', str(pr_number), 'comments')
        params = {'page': '1', 'limit': '100', 'order': 'asc'}

        response, _ = await self._make_request(url, params)
        raw_comments = response if isinstance(response, list) else []

        grouped: dict[str, list[str]] = defaultdict(list)
        files: dict[str, set[str]] = defaultdict(set)

        for payload in raw_comments:
            if not isinstance(payload, dict):
                continue
            path = cast(str, payload.get('path') or 'general')
            body = cast(str, payload.get('body') or '')
            grouped[path].append(body)
            if payload.get('path'):
                files[path].add(cast(str, payload['path']))

        threads: list[ReviewThread] = []
        for path, messages in grouped.items():
            comment_text = '\n---\n'.join(messages)
            file_list = sorted(files.get(path, {path}))
            threads.append(ReviewThread(comment=comment_text, files=file_list))

        return threads[:max_threads]