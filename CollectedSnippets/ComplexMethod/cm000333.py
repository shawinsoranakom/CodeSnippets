async def create_test_store_submissions(self) -> List[Dict[str, Any]]:
        """Create test store submissions using the API function.

        DETERMINISTIC: Guarantees minimum featured agents for E2E tests.
        """
        print("Creating test store submissions...")

        submissions = []
        approved_submissions = []
        featured_count = 0
        submission_counter = 0

        # Create a deterministic calculator marketplace agent for PR E2E coverage
        test_user = next(
            (
                user
                for user in self.users
                if user["email"] == E2E_MARKETPLACE_CREATOR_EMAIL
            ),
            None,
        )
        if test_user:
            deterministic_graph = None

            try:
                existing_graph = await prisma_models.AgentGraph.prisma().find_first(
                    where={
                        "userId": test_user["id"],
                        "name": E2E_MARKETPLACE_AGENT_NAME,
                        "isActive": True,
                    },
                    order={"version": "desc"},
                )
                if existing_graph:
                    deterministic_graph = {
                        "id": existing_graph.id,
                        "version": existing_graph.version,
                        "name": existing_graph.name,
                        "userId": test_user["id"],
                    }
                    self.agent_graphs.append(deterministic_graph)
                    print(
                        "✅ Reused existing deterministic marketplace graph: "
                        f"{existing_graph.id}"
                    )
                else:
                    deterministic_graph_model = make_graph_model(
                        load_deterministic_marketplace_graph(),
                        test_user["id"],
                    )
                    deterministic_graph_model.reassign_ids(
                        user_id=test_user["id"],
                        reassign_graph_id=True,
                    )
                    created_deterministic_graph = await create_graph(
                        deterministic_graph_model,
                        test_user["id"],
                    )
                    deterministic_graph = created_deterministic_graph.model_dump()
                    deterministic_graph["userId"] = test_user["id"]
                    self.agent_graphs.append(deterministic_graph)
                    print("✅ Created deterministic marketplace graph")
            except Exception as e:
                print(f"Error creating deterministic marketplace graph: {e}")

            if deterministic_graph is None and self.agent_graphs:
                test_user_graphs = [
                    graph
                    for graph in self.agent_graphs
                    if graph.get("userId") == test_user["id"]
                ]
                deterministic_graph = next(
                    (
                        graph
                        for graph in test_user_graphs
                        if not graph.get("name", "").startswith("DummyInput ")
                    ),
                    test_user_graphs[0] if test_user_graphs else None,
                )

            if deterministic_graph:
                test_submission_data = {
                    "user_id": test_user["id"],
                    "graph_id": deterministic_graph["id"],
                    "graph_version": deterministic_graph.get("version", 1),
                    "slug": E2E_MARKETPLACE_AGENT_SLUG,
                    "name": E2E_MARKETPLACE_AGENT_NAME,
                    "sub_heading": "A deterministic calculator agent for PR E2E coverage",
                    "video_url": "https://www.youtube.com/watch?v=test123",
                    "image_urls": [
                        "https://picsum.photos/seed/e2e-marketplace-1/200/300",
                        "https://picsum.photos/seed/e2e-marketplace-2/200/301",
                        "https://picsum.photos/seed/e2e-marketplace-3/200/302",
                    ],
                    "description": (
                        "A deterministic marketplace calculator agent that adds "
                        f"{E2E_MARKETPLACE_AGENT_INPUT_VALUE} and 34 to produce "
                        f"{E2E_MARKETPLACE_AGENT_OUTPUT_VALUE} for frontend E2E coverage."
                    ),
                    "categories": ["test", "demo", "frontend"],
                    "changes_summary": (
                        "Initial deterministic calculator submission seeded from "
                        "backend/agents/calculator-agent.json"
                    ),
                }

                try:
                    existing_deterministic_submission = (
                        await prisma_models.StoreListingVersion.prisma().find_first(
                            where={
                                "isDeleted": False,
                                "StoreListing": {
                                    "is": {
                                        "owningUserId": test_user["id"],
                                        "slug": E2E_MARKETPLACE_AGENT_SLUG,
                                        "isDeleted": False,
                                    }
                                },
                            },
                            include={"StoreListing": True},
                            order={"version": "desc"},
                        )
                    )

                    if existing_deterministic_submission:
                        test_submission = StoreSubmission.from_listing_version(
                            existing_deterministic_submission
                        )
                        submissions.append(test_submission.model_dump())
                        print(
                            "✅ Reused deterministic marketplace submission: "
                            f"{E2E_MARKETPLACE_AGENT_NAME}"
                        )
                    else:
                        test_submission = await create_store_submission(
                            **test_submission_data
                        )
                        submissions.append(test_submission.model_dump())
                        print(
                            "✅ Created deterministic marketplace submission: "
                            f"{E2E_MARKETPLACE_AGENT_NAME}"
                        )

                    current_status = (
                        existing_deterministic_submission.submissionStatus
                        if existing_deterministic_submission
                        else test_submission.status
                    )
                    is_featured = bool(
                        existing_deterministic_submission
                        and existing_deterministic_submission.isFeatured
                    )

                    if test_submission.listing_version_id:
                        if current_status != prisma_enums.SubmissionStatus.APPROVED:
                            approved_submission = await review_store_submission(
                                store_listing_version_id=test_submission.listing_version_id,
                                is_approved=True,
                                external_comments="Deterministic calculator submission approved",
                                internal_comments="Auto-approved PR E2E marketplace submission",
                                reviewer_id=test_user["id"],
                            )
                            approved_submissions.append(
                                approved_submission.model_dump()
                            )
                            print("✅ Approved deterministic marketplace submission")
                        else:
                            approved_submissions.append(test_submission.model_dump())
                            print(
                                "✅ Deterministic marketplace submission already approved"
                            )

                        if is_featured:
                            featured_count += 1
                            print("🌟 Deterministic marketplace agent already FEATURED")
                        else:
                            await prisma.storelistingversion.update(
                                where={"id": test_submission.listing_version_id},
                                data={"isFeatured": True},
                            )
                            featured_count += 1
                            print(
                                "🌟 Marked deterministic marketplace agent as FEATURED"
                            )

                except Exception as e:
                    print(f"Error creating deterministic marketplace submission: {e}")
                    import traceback

                    traceback.print_exc()

        # Create regular submissions for all users
        for user in self.users:
            user_graphs = [
                g for g in self.agent_graphs if g.get("userId") == user["id"]
            ]
            print(f"User {user['id']} has {len(user_graphs)} graphs")
            if not user_graphs:
                print(
                    f"No graphs found for user {user['id']}, skipping store submissions"
                )
                continue

            for submission_index in range(4):
                graph = random.choice(user_graphs)
                submission_counter += 1

                try:
                    print(
                        f"Creating store submission for user {user['id']} with graph {graph['id']}"
                    )

                    submission = await create_store_submission(
                        user_id=user["id"],
                        graph_id=graph["id"],
                        graph_version=graph.get("version", 1),
                        slug=faker.slug(),
                        name=graph.get("name", faker.sentence(nb_words=3)),
                        sub_heading=faker.sentence(),
                        video_url=get_video_url() if random.random() < 0.3 else None,
                        image_urls=[get_image() for _ in range(3)],
                        description=faker.text(),
                        categories=[get_category()],
                        changes_summary="Initial E2E test submission",
                    )
                    submissions.append(submission.model_dump())
                    print(f"✅ Created store submission: {submission.name}")

                    if submission.listing_version_id:
                        # DETERMINISTIC: First N submissions are always approved
                        # First GUARANTEED_FEATURED_AGENTS of those are always featured
                        should_approve = (
                            submission_counter <= GUARANTEED_TOP_AGENTS
                            or random.random() < 0.4
                        )
                        should_feature = featured_count < GUARANTEED_FEATURED_AGENTS

                        if should_approve:
                            try:
                                reviewer_id = random.choice(self.users)["id"]
                                approved_submission = await review_store_submission(
                                    store_listing_version_id=submission.listing_version_id,
                                    is_approved=True,
                                    external_comments="Auto-approved for E2E testing",
                                    internal_comments="Automatically approved by E2E test data script",
                                    reviewer_id=reviewer_id,
                                )
                                approved_submissions.append(
                                    approved_submission.model_dump()
                                )
                                print(
                                    f"✅ Approved store submission: {submission.name}"
                                )

                                if should_feature:
                                    try:
                                        await prisma.storelistingversion.update(
                                            where={"id": submission.listing_version_id},
                                            data={"isFeatured": True},
                                        )
                                        featured_count += 1
                                        print(
                                            f"🌟 Marked agent as FEATURED ({featured_count}/{GUARANTEED_FEATURED_AGENTS}): {submission.name}"
                                        )
                                    except Exception as e:
                                        print(
                                            f"Warning: Could not mark submission as featured: {e}"
                                        )
                                elif random.random() < 0.2:
                                    try:
                                        await prisma.storelistingversion.update(
                                            where={"id": submission.listing_version_id},
                                            data={"isFeatured": True},
                                        )
                                        featured_count += 1
                                        print(
                                            f"🌟 Marked agent as FEATURED (bonus): {submission.name}"
                                        )
                                    except Exception as e:
                                        print(
                                            f"Warning: Could not mark submission as featured: {e}"
                                        )

                            except Exception as e:
                                print(
                                    f"Warning: Could not approve submission {submission.name}: {e}"
                                )
                        elif random.random() < 0.5:
                            try:
                                reviewer_id = random.choice(self.users)["id"]
                                await review_store_submission(
                                    store_listing_version_id=submission.listing_version_id,
                                    is_approved=False,
                                    external_comments="Submission rejected - needs improvements",
                                    internal_comments="Automatically rejected by E2E test data script",
                                    reviewer_id=reviewer_id,
                                )
                                print(
                                    f"❌ Rejected store submission: {submission.name}"
                                )
                            except Exception as e:
                                print(
                                    f"Warning: Could not reject submission {submission.name}: {e}"
                                )
                        else:
                            print(
                                f"⏳ Left submission pending for review: {submission.name}"
                            )

                except Exception as e:
                    print(
                        f"Error creating store submission for user {user['id']} graph {graph['id']}: {e}"
                    )
                    import traceback

                    traceback.print_exc()
                    continue

        print("\n📊 Store Submissions Summary:")
        print(f"   Created: {len(submissions)}")
        print(f"   Approved: {len(approved_submissions)}")
        print(
            f"   Featured: {featured_count} (guaranteed min: {GUARANTEED_FEATURED_AGENTS})"
        )

        self.store_submissions = submissions
        return submissions