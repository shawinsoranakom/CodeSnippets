async def add_test_data(db):
    """Add some test data to verify materialized view updates."""
    print("\n3. Adding test data...")
    print("-" * 40)

    # Get some existing data
    users = await db.user.find_many(take=5)
    graphs = await db.agentgraph.find_many(take=5)

    if not users or not graphs:
        print("❌ No existing users or graphs found. Run test_data_creator.py first.")
        return False

    # Add new executions
    print("Adding new agent graph executions...")
    new_executions = 0
    for graph in graphs:
        for _ in range(random.randint(2, 5)):
            await db.agentgraphexecution.create(
                data={
                    "agentGraphId": graph.id,
                    "agentGraphVersion": graph.version,
                    "userId": random.choice(users).id,
                    "executionStatus": "COMPLETED",
                    "startedAt": datetime.now(),
                }
            )
            new_executions += 1

    print(f"✅ Added {new_executions} new executions")

    # Check if we need to create store listings first
    store_versions = await db.storelistingversion.find_many(
        where={"submissionStatus": "APPROVED"}, take=5
    )

    if not store_versions:
        print("\nNo approved store listings found. Creating test store listings...")

        # Create store listings for existing agent graphs
        for i, graph in enumerate(graphs[:3]):  # Create up to 3 store listings
            # Create a store listing
            listing = await db.storelisting.create(
                data={
                    "slug": f"test-agent-{graph.id[:8]}",
                    "agentGraphId": graph.id,
                    "agentGraphVersion": graph.version,
                    "hasApprovedVersion": True,
                    "owningUserId": graph.userId,
                }
            )

            # Create an approved version
            version = await db.storelistingversion.create(
                data={
                    "storeListingId": listing.id,
                    "agentGraphId": graph.id,
                    "agentGraphVersion": graph.version,
                    "name": f"Test Agent {i+1}",
                    "subHeading": faker.catch_phrase(),
                    "description": faker.paragraph(nb_sentences=5),
                    "imageUrls": [faker.image_url()],
                    "categories": ["productivity", "automation"],
                    "submissionStatus": "APPROVED",
                    "submittedAt": datetime.now(),
                }
            )

            # Update listing with active version
            await db.storelisting.update(
                where={"id": listing.id}, data={"activeVersionId": version.id}
            )

        print("✅ Created test store listings")

        # Re-fetch approved versions
        store_versions = await db.storelistingversion.find_many(
            where={"submissionStatus": "APPROVED"}, take=5
        )

    # Add new reviews
    print("\nAdding new store listing reviews...")
    new_reviews = 0
    for version in store_versions:
        # Find users who haven't reviewed this version
        existing_reviews = await db.storelistingreview.find_many(
            where={"storeListingVersionId": version.id}
        )
        reviewed_user_ids = {r.reviewByUserId for r in existing_reviews}
        available_users = [u for u in users if u.id not in reviewed_user_ids]

        if available_users:
            user = random.choice(available_users)
            await db.storelistingreview.create(
                data={
                    "storeListingVersionId": version.id,
                    "reviewByUserId": user.id,
                    "score": random.randint(3, 5),
                    "comments": faker.text(max_nb_chars=100),
                }
            )
            new_reviews += 1

    print(f"✅ Added {new_reviews} new reviews")

    return True