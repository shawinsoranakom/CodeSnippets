def _fetch_from_gitlab(
        self, start: datetime | None = None, end: datetime | None = None
    ) -> GenerateDocumentsOutput:
        if self.gitlab_client is None:
            raise ConnectorMissingCredentialError("Gitlab")
        project: Project = self.gitlab_client.projects.get(
            f"{self.project_owner}/{self.project_name}"
        )

        start_utc = start.astimezone(timezone.utc) if start else None
        end_utc = end.astimezone(timezone.utc) if end else None

        # Fetch code files
        if self.include_code_files:
            # Fetching using BFS as project.report_tree with recursion causing slow load
            queue = deque([""])  # Start with the root directory
            while queue:
                current_path = queue.popleft()
                files = project.repository_tree(path=current_path, all=True)
                for file_batch in _batch_gitlab_objects(files, self.batch_size):
                    code_doc_batch: list[Document] = []
                    for file in file_batch:
                        if _should_exclude(file["path"]):
                            continue

                        if file["type"] == "blob":

                            doc = _convert_code_to_document(
                                project,
                                file,
                                self.gitlab_client.url,
                                self.project_name,
                                self.project_owner,
                            )

                            # Apply incremental window filtering for code files too.
                            if start_utc is not None and doc.doc_updated_at <= start_utc:
                                continue
                            if end_utc is not None and doc.doc_updated_at > end_utc:
                                continue

                            code_doc_batch.append(doc)
                        elif file["type"] == "tree":
                            queue.append(file["path"])

                    if code_doc_batch:
                        yield code_doc_batch

        if self.include_mrs:
            merge_requests = project.mergerequests.list(
                state=self.state_filter,
                order_by="updated_at",
                sort="desc",
                iterator=True,
            )

            for mr_batch in _batch_gitlab_objects(merge_requests, self.batch_size):
                mr_doc_batch: list[Document] = []
                for mr in mr_batch:
                    mr.updated_at = datetime.strptime(
                        mr.updated_at, "%Y-%m-%dT%H:%M:%S.%f%z"
                    )
                    if start_utc is not None and mr.updated_at <= start_utc:
                        yield mr_doc_batch
                        return
                    if end_utc is not None and mr.updated_at > end_utc:
                        continue
                    mr_doc_batch.append(_convert_merge_request_to_document(mr))
                yield mr_doc_batch

        if self.include_issues:
            issues = project.issues.list(state=self.state_filter, iterator=True)

            for issue_batch in _batch_gitlab_objects(issues, self.batch_size):
                issue_doc_batch: list[Document] = []
                for issue in issue_batch:
                    issue.updated_at = datetime.strptime(
                        issue.updated_at, "%Y-%m-%dT%H:%M:%S.%f%z"
                    )
                    # Avoid re-syncing the last-seen item.
                    if start_utc is not None and issue.updated_at <= start_utc:
                        yield issue_doc_batch
                        return
                    if end_utc is not None and issue.updated_at > end_utc:
                        continue
                    issue_doc_batch.append(_convert_issue_to_document(issue))
                yield issue_doc_batch