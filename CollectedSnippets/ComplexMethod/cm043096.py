def main():
    """Run the webhook demonstration"""

    # Check if Crawl4AI is running
    try:
        health = requests.get(f"{CRAWL4AI_BASE_URL}/health", timeout=5)
        print(f"✅ Crawl4AI is running: {health.json()}")
    except:
        print(f"❌ Cannot connect to Crawl4AI at {CRAWL4AI_BASE_URL}")
        print("   Please make sure Docker container is running:")
        print("   docker run -d -p 11235:11235 --name crawl4ai unclecode/crawl4ai:latest")
        return

    # Start webhook server in background thread
    print(f"\n🌐 Starting webhook server at {WEBHOOK_BASE_URL}...")
    webhook_thread = Thread(target=start_webhook_server, daemon=True)
    webhook_thread.start()
    time.sleep(2)  # Give server time to start

    # Example 1: Job with webhook (notification only, fetch data separately)
    print(f"\n{'='*60}")
    print("Example 1: Webhook Notification Only")
    print(f"{'='*60}")
    task_id_1 = submit_crawl_job_with_webhook(
        urls=["https://example.com"],
        webhook_url=f"{WEBHOOK_BASE_URL}/webhooks/crawl-complete",
        include_data=False
    )

    # Example 2: Job with webhook (data included in payload)
    time.sleep(5)  # Wait a bit between requests
    print(f"\n{'='*60}")
    print("Example 2: Webhook with Full Data")
    print(f"{'='*60}")
    task_id_2 = submit_crawl_job_with_webhook(
        urls=["https://www.python.org"],
        webhook_url=f"{WEBHOOK_BASE_URL}/webhooks/crawl-complete",
        include_data=True
    )

    # Example 3: LLM extraction with webhook (notification only)
    time.sleep(5)  # Wait a bit between requests
    print(f"\n{'='*60}")
    print("Example 3: LLM Extraction with Webhook (Notification Only)")
    print(f"{'='*60}")
    task_id_3 = submit_llm_job_with_webhook(
        url="https://www.example.com",
        query="Extract the main heading and description from this page.",
        webhook_url=f"{WEBHOOK_BASE_URL}/webhooks/llm-complete",
        include_data=False,
        provider="openai/gpt-4o-mini"
    )

    # Example 4: LLM extraction with webhook (data included + schema)
    time.sleep(5)  # Wait a bit between requests
    print(f"\n{'='*60}")
    print("Example 4: LLM Extraction with Schema and Full Data")
    print(f"{'='*60}")

    # Define a schema for structured extraction
    schema = json.dumps({
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Page title"},
            "description": {"type": "string", "description": "Page description"}
        },
        "required": ["title"]
    })

    task_id_4 = submit_llm_job_with_webhook(
        url="https://www.python.org",
        query="Extract the title and description of this website",
        webhook_url=f"{WEBHOOK_BASE_URL}/webhooks/llm-complete",
        include_data=True,
        schema=schema,
        provider="openai/gpt-4o-mini"
    )

    # Example 5: Traditional polling (no webhook)
    time.sleep(5)  # Wait a bit between requests
    print(f"\n{'='*60}")
    print("Example 5: Traditional Polling (No Webhook)")
    print(f"{'='*60}")
    task_id_5 = submit_job_without_webhook(
        urls=["https://github.com"]
    )
    if task_id_5:
        result = poll_job_status(task_id_5)
        if result and result.get('status') == 'completed':
            print(f"   ✅ Results retrieved via polling")

    # Wait for webhooks to arrive
    print(f"\n⏳ Waiting for webhooks to be received...")
    time.sleep(30)  # Give jobs time to complete and webhooks to arrive (longer for LLM)

    # Summary
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    print(f"Total webhooks received: {len(received_webhooks)}")

    crawl_webhooks = [w for w in received_webhooks if w['task_type'] == 'crawl']
    llm_webhooks = [w for w in received_webhooks if w['task_type'] == 'llm_extraction']

    print(f"\n📊 Breakdown:")
    print(f"   - Crawl webhooks: {len(crawl_webhooks)}")
    print(f"   - LLM extraction webhooks: {len(llm_webhooks)}")

    print(f"\n📋 Details:")
    for i, webhook in enumerate(received_webhooks, 1):
        task_type = webhook['task_type']
        icon = "🕷️" if task_type == "crawl" else "🤖"
        print(f"{i}. {icon} Task {webhook['task_id']}: {webhook['status']} ({task_type})")

    print(f"\n✅ Demo completed!")
    print(f"\n💡 Pro tips:")
    print(f"   - In production, your webhook URL should be publicly accessible")
    print(f"     (e.g., https://myapp.com/webhooks) or use ngrok for testing")
    print(f"   - Both /crawl/job and /llm/job support the same webhook configuration")
    print(f"   - Use webhook_data_in_payload=true to get results directly in the webhook")
    print(f"   - LLM jobs may take longer, adjust timeouts accordingly")