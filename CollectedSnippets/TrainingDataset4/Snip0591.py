 async def create_test_store_submissions(self) -> List[Dict[str, Any]]:
        """Create test store submissions using the API function."""
        print("Creating test store submissions...")

        submissions = []
        approved_submissions = []

        # Create a special test submission for test123@gmail.com
        test_user = next(
            (user for user in self.users if user["email"] == "test123@gmail.com"), None
        )
        if test_user:
            # Special test data for consistent testing
            test_submission_data = {
                "user_id": test_user["id"],
                "agent_id": self.agent_graphs[0]["id"],  # Use first available graph
                "agent_version": 1,
                "slug": "test-agent-submission",
                "name": "Test Agent Submission",
                "sub_heading": "A test agent for frontend testing",
                "video_url": "https://www.youtube.com/watch?v=test123",
                "image_urls": [
                    "https://picsum.photos/200/300",
                    "https://picsum.photos/200/301",
                    "https://picsum.photos/200/302",
                ],
                "description": "This is a test agent submission specifically created for frontend testing purposes.",
                "categories": ["test", "demo", "frontend"],
                "changes_summary": "Initial test submission",
            }

            try:
                test_submission = await create_store_submission(**test_submission_data)
                submissions.append(test_submission.model_dump())
                print("✅ Created special test store submission for test123@gmail.com")

                # Randomly approve, reject, or leave pending the test submission
                if test_submission.store_listing_version_id:
                    random_value = random.random()
                    if random_value < 0.4:  # 40% chance to approve
                        approved_submission = await review_store_submission(
                            store_listing_version_id=test_submission.store_listing_version_id,
                            is_approved=True,
                            external_comments="Test submission approved",
                            internal_comments="Auto-approved test submission",
                            reviewer_id=test_user["id"],
                        )
                        approved_submissions.append(approved_submission.model_dump())
                        print("✅ Approved test store submission")

                        # Mark approved submission as featured
                        await prisma.storelistingversion.update(
                            where={"id": test_submission.store_listing_version_id},
                            data={"isFeatured": True},
                        )
                        print("🌟 Marked test agent as FEATURED")
                    elif random_value < 0.7:  # 30% chance to reject (40% to 70%)
                        await review_store_submission(
                            store_listing_version_id=test_submission.store_listing_version_id,
                            is_approved=False,
                            external_comments="Test submission rejected - needs improvements",
                            internal_comments="Auto-rejected test submission for E2E testing",
                            reviewer_id=test_user["id"],
                        )
                        print("❌ Rejected test store submission")
                    else:  # 30% chance to leave pending (70% to 100%)
                        print("⏳ Left test submission pending for review")

            except Exception as e:
                print(f"Error creating test store submission: {e}")
                import traceback

                traceback.print_exc()

        # Create regular submissions for all users
        for user in self.users:
            # Get available graphs for this specific user
            user_graphs = [
                g for g in self.agent_graphs if g.get("userId") == user["id"]
            ]
            print(f"User {user['id']} has {len(user_graphs)} graphs")
            if not user_graphs:
                print(
                    f"No graphs found for user {user['id']}, skipping store submissions"
                )
                continue

            # Create exactly 4 store submissions per user
            for submission_index in range(4):
                graph = random.choice(user_graphs)

                try:
                    print(
                        f"Creating store submission for user {user['id']} with graph {graph['id']} (owner: {graph.get('userId')})"
                    )

                    # Use the API function to create store submission with correct parameters
                    submission = await create_store_submission(
                        user_id=user["id"],  # Must match graph's userId
                        agent_id=graph["id"],
                        agent_version=graph.get("version", 1),
                        slug=faker.slug(),
                        name=graph.get("name", faker.sentence(nb_words=3)),
                        sub_heading=faker.sentence(),
                        video_url=get_video_url() if random.random() < 0.3 else None,
                        image_urls=[get_image() for _ in range(3)],
                        description=faker.text(),
                        categories=[
                            get_category()
                        ],  # Single category from predefined list
                        changes_summary="Initial E2E test submission",
                    )
                    submissions.append(submission.model_dump())
                    print(f"✅ Created store submission: {submission.name}")

                    # Randomly approve, reject, or leave pending the submission
                    if submission.store_listing_version_id:
                        random_value = random.random()
                        if random_value < 0.4:  # 40% chance to approve
                            try:
                                # Pick a random user as the reviewer (admin)
                                reviewer_id = random.choice(self.users)["id"]

                                approved_submission = await review_store_submission(
                                    store_listing_version_id=submission.store_listing_version_id,
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

                                # Mark some agents as featured during creation (30% chance)
                                # More likely for creators and first submissions
                                is_creator = user["id"] in [
                                    p.get("userId") for p in self.profiles
                                ]
                                feature_chance = (
                                    0.5 if is_creator else 0.2
                                )  # 50% for creators, 20% for others

                                if random.random() < feature_chance:
                                    try:
                                        await prisma.storelistingversion.update(
                                            where={
                                                "id": submission.store_listing_version_id
                                            },
                                            data={"isFeatured": True},
                                        )
                                        print(
                                            f"🌟 Marked agent as FEATURED: {submission.name}"
                                        )
                                    except Exception as e:
                                        print(
                                            f"Warning: Could not mark submission as featured: {e}"
                                        )

                            except Exception as e:
                                print(
                                    f"Warning: Could not approve submission {submission.name}: {e}"
                                )
                        elif random_value < 0.7:  # 30% chance to reject (40% to 70%)
                            try:
                                # Pick a random user as the reviewer (admin)
                                reviewer_id = random.choice(self.users)["id"]

                                await review_store_submission(
                                    store_listing_version_id=submission.store_listing_version_id,
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
                        else:  # 30% chance to leave pending (70% to 100%)
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

        print(
            f"Created {len(submissions)} store submissions, approved {len(approved_submissions)}"
        )
        self.store_submissions = submissions
        return submissions
