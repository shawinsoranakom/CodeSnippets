async def main():
    db = Prisma()
    await db.connect()

    print("Starting test data updates for materialized views...")
    print("=" * 60)

    # Get existing data
    users = await db.user.find_many(take=50)
    agent_graphs = await db.agentgraph.find_many(where={"isActive": True}, take=50)
    store_listings = await db.storelisting.find_many(
        where={"hasApprovedVersion": True}, include={"Versions": True}, take=30
    )
    agent_nodes = await db.agentnode.find_many(take=100)

    if not all([users, agent_graphs, store_listings]):
        print(
            "ERROR: Not enough test data found. Please run test_data_creator.py first."
        )
        await db.disconnect()
        return

    print(
        f"Found {len(users)} users, {len(agent_graphs)} graphs, {len(store_listings)} store listings"
    )
    print()

    # 1. Add new AgentGraphExecutions to update mv_agent_run_counts
    print("1. Adding new agent graph executions...")
    print("-" * 40)

    new_executions_count = 0
    execution_data = []

    for graph in random.sample(agent_graphs, min(20, len(agent_graphs))):
        # Add 5-15 new executions per selected graph
        num_new_executions = random.randint(5, 15)
        for _ in range(num_new_executions):
            user = random.choice(users)
            execution_data.append(
                {
                    "agentGraphId": graph.id,
                    "agentGraphVersion": graph.version,
                    "userId": user.id,
                    "executionStatus": random.choice(
                        [
                            prisma.enums.AgentExecutionStatus.COMPLETED,
                            prisma.enums.AgentExecutionStatus.FAILED,
                            prisma.enums.AgentExecutionStatus.RUNNING,
                        ]
                    ),
                    "startedAt": faker.date_time_between(
                        start_date="-7d", end_date="now"
                    ),
                    "stats": Json(
                        {
                            "duration": random.randint(100, 5000),
                            "blocks_executed": random.randint(1, 10),
                        }
                    ),
                }
            )
            new_executions_count += 1

    # Batch create executions
    await db.agentgraphexecution.create_many(data=execution_data)
    print(f"✓ Created {new_executions_count} new executions")

    # Get the created executions for node executions
    recent_executions = await db.agentgraphexecution.find_many(
        take=new_executions_count, order={"createdAt": "desc"}
    )

    # 2. Add corresponding AgentNodeExecutions
    print("\n2. Adding agent node executions...")
    print("-" * 40)

    node_execution_data = []
    for execution in recent_executions:
        # Get nodes for this graph
        graph_nodes = [
            n for n in agent_nodes if n.agentGraphId == execution.agentGraphId
        ]
        if graph_nodes:
            for node in random.sample(graph_nodes, min(3, len(graph_nodes))):
                node_execution_data.append(
                    {
                        "agentGraphExecutionId": execution.id,
                        "agentNodeId": node.id,
                        "executionStatus": execution.executionStatus,
                        "addedTime": datetime.now(),
                        "startedTime": datetime.now()
                        - timedelta(minutes=random.randint(1, 10)),
                        "endedTime": (
                            datetime.now()
                            if execution.executionStatus
                            == prisma.enums.AgentExecutionStatus.COMPLETED
                            else None
                        ),
                    }
                )

    await db.agentnodeexecution.create_many(data=node_execution_data)
    print(f"✓ Created {len(node_execution_data)} node executions")

    # 3. Add new StoreListingReviews to update mv_review_stats
    print("\n3. Adding new store listing reviews...")
    print("-" * 40)

    new_reviews_count = 0

    for listing in store_listings:
        if not listing.Versions:
            continue

        # Get approved versions
        approved_versions = [
            v
            for v in listing.Versions
            if v.submissionStatus == prisma.enums.SubmissionStatus.APPROVED
        ]
        if not approved_versions:
            continue

        # Pick a version to add reviews to
        version = random.choice(approved_versions)

        # Get existing reviews for this version to avoid duplicates
        existing_reviews = await db.storelistingreview.find_many(
            where={"storeListingVersionId": version.id}
        )
        existing_reviewer_ids = {r.reviewByUserId for r in existing_reviews}

        # Find users who haven't reviewed this version yet
        available_reviewers = [u for u in users if u.id not in existing_reviewer_ids]

        if available_reviewers:
            # Add 2-5 new reviews
            num_new_reviews = min(random.randint(2, 5), len(available_reviewers))
            selected_reviewers = random.sample(available_reviewers, num_new_reviews)

            for reviewer in selected_reviewers:
                # Bias towards positive reviews (4-5 stars)
                score = random.choices([1, 2, 3, 4, 5], weights=[5, 10, 20, 40, 25])[0]

                await db.storelistingreview.create(
                    data={
                        "storeListingVersionId": version.id,
                        "reviewByUserId": reviewer.id,
                        "score": score,
                        "comments": (
                            faker.text(max_nb_chars=200)
                            if random.random() < 0.7
                            else None
                        ),
                    }
                )
                new_reviews_count += 1

    print(f"✓ Created {new_reviews_count} new reviews")

    # 4. Update some store listing versions (change categories, featured status)
    print("\n4. Updating store listing versions...")
    print("-" * 40)

    updates_count = 0
    for listing in random.sample(store_listings, min(10, len(store_listings))):
        if listing.Versions:
            version = random.choice(listing.Versions)
            if version.submissionStatus == prisma.enums.SubmissionStatus.APPROVED:
                # Toggle featured status or update categories
                new_categories = random.sample(
                    [
                        "productivity",
                        "ai",
                        "automation",
                        "data",
                        "social",
                        "marketing",
                        "development",
                        "analytics",
                    ],
                    k=random.randint(2, 4),
                )

                await db.storelistingversion.update(
                    where={"id": version.id},
                    data={
                        "isFeatured": (
                            not version.isFeatured
                            if random.random() < 0.3
                            else version.isFeatured
                        ),
                        "categories": new_categories,
                        "updatedAt": datetime.now(),
                    },
                )
                updates_count += 1
