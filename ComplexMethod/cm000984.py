async def _execute(
        self,
        user_id: str | None,
        session: ChatSession,
        title: str = "",
        description: str = "",
        existing_issue_id: str | None = None,
        **kwargs,
    ) -> ToolResponseBase:
        title = (title or "").strip()
        description = (description or "").strip()
        session_id = session.session_id if session else None

        if not title or not description:
            return ErrorResponse(
                message="Both title and description are required.",
                error="Missing required parameters",
                session_id=session_id,
            )

        if not user_id:
            return ErrorResponse(
                message="Authentication required to create feature requests.",
                error="Missing user_id",
                session_id=session_id,
            )

        try:
            client, project_id, team_id = _get_linear_config()
        except Exception as e:
            logger.exception("Failed to initialize Linear client")
            return ErrorResponse(
                message="Failed to create feature request.",
                error=str(e),
                session_id=session_id,
            )

        # Resolve a human-readable name (email) for the Linear customer record.
        # Fall back to user_id if the lookup fails or returns None.
        try:
            customer_display_name = (
                await user_db().get_user_email_by_id(user_id) or user_id
            )
        except Exception:
            customer_display_name = user_id

        # Step 1: Find or create customer for this user
        try:
            customer = await self._find_or_create_customer(
                client, user_id, customer_display_name
            )
            customer_id = customer["id"]
            customer_name = customer["name"]
        except Exception as e:
            logger.exception("Failed to upsert customer in Linear")
            return ErrorResponse(
                message="Failed to create feature request.",
                error=str(e),
                session_id=session_id,
            )

        # Step 2: Create or reuse issue
        issue_id: str | None = None
        issue_identifier: str | None = None
        if existing_issue_id:
            # Add need to existing issue - we still need the issue details for response
            is_new_issue = False
            issue_id = existing_issue_id
        else:
            # Create new issue in the feature requests project
            try:
                data = await client.mutate(
                    ISSUE_CREATE_MUTATION,
                    {
                        "input": {
                            "title": title,
                            "description": description,
                            "teamId": team_id,
                            "projectId": project_id,
                        },
                    },
                )
                result = data.get("issueCreate", {})
                if not result.get("success"):
                    return ErrorResponse(
                        message="Failed to create feature request issue.",
                        error=str(data),
                        session_id=session_id,
                    )
                issue = result["issue"]
                issue_id = issue["id"]
                issue_identifier = issue.get("identifier")
            except Exception as e:
                logger.exception("Failed to create feature request issue")
                return ErrorResponse(
                    message="Failed to create feature request.",
                    error=str(e),
                    session_id=session_id,
                )
            is_new_issue = True

        # Step 3: Create customer need on the issue
        try:
            data = await client.mutate(
                CUSTOMER_NEED_CREATE_MUTATION,
                {
                    "input": {
                        "customerId": customer_id,
                        "issueId": issue_id,
                        "body": description,
                        "priority": 0,
                    },
                },
            )
            need_result = data.get("customerNeedCreate", {})
            if not need_result.get("success"):
                orphaned = (
                    {"issue_id": issue_id, "issue_identifier": issue_identifier}
                    if is_new_issue
                    else None
                )
                return ErrorResponse(
                    message="Failed to attach customer need to the feature request.",
                    error=str(data),
                    details=orphaned,
                    session_id=session_id,
                )
            need = need_result["need"]
            issue_info = need["issue"]
        except Exception as e:
            logger.exception("Failed to create customer need")
            orphaned = (
                {"issue_id": issue_id, "issue_identifier": issue_identifier}
                if is_new_issue
                else None
            )
            return ErrorResponse(
                message="Failed to attach customer need to the feature request.",
                error=str(e),
                details=orphaned,
                session_id=session_id,
            )

        return FeatureRequestCreatedResponse(
            message=(
                f"{'Created new feature request' if is_new_issue else 'Added your request to existing feature request'}: "
                f"{issue_info['title']}."
            ),
            issue_id=issue_info["id"],
            issue_identifier=issue_info["identifier"],
            issue_title=issue_info["title"],
            issue_url=issue_info.get("url", ""),
            is_new_issue=is_new_issue,
            customer_name=customer_name,
            session_id=session_id,
        )