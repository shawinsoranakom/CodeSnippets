async def memory_inspection():
    """Demonstrates get_items with limit parameter and detailed memory analysis"""

    session = SQLiteSession("inspection_demo", "inspection.db")

    print("\n=== Advanced Memory Inspection ===")

    # Build longer conversation for inspection
    conversation_items = [
        "Hello, I'm learning about AI.",
        "What is machine learning?",
        "How does deep learning work?", 
        "What's the difference between AI and ML?",
        "Can you explain neural networks?"
    ]

    print("🏗️  Building extended conversation...")
    for item in conversation_items:
        await Runner.run(root_agent, item, session=session)

    # Demonstrate get_items() with limit parameter (from SDK docs)
    print(f"\n🔍 Memory Inspection with get_items(limit=3):")
    recent_items = await session.get_items(limit=3)
    print(f"   Last 3 items (out of full conversation):")
    for i, item in enumerate(recent_items, 1):
        content_preview = item['content'][:60] + "..." if len(item['content']) > 60 else item['content']
        print(f"   {i}. [{item['role']}]: {content_preview}")

    # Compare with full conversation
    all_items = await session.get_items()
    print(f"\n📊 Full conversation analysis:")
    print(f"   Total items in session: {len(all_items)}")
    print(f"   Recent items retrieved: {len(recent_items)}")

    # Count items by role
    user_items = [item for item in all_items if item['role'] == 'user']
    assistant_items = [item for item in all_items if item['role'] == 'assistant']
    print(f"   User messages: {len(user_items)}")
    print(f"   Assistant responses: {len(assistant_items)}")

    return session