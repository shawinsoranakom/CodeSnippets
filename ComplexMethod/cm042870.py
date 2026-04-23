def test_pattern_consistency():
    """Test that /llm/job follows the same pattern as /crawl/job"""
    print("\n" + "=" * 60)
    print("TEST 7: Pattern Consistency with /crawl/job")
    print("=" * 60)

    try:
        api_file = os.path.join(os.path.dirname(__file__), 'deploy', 'docker', 'api.py')

        with open(api_file, 'r') as f:
            api_content = f.read()

        # Find handle_crawl_job to compare pattern
        crawl_job_start = api_content.find('async def handle_crawl_job')
        crawl_job_end = api_content.find('\nasync def ', crawl_job_start + 1)
        if crawl_job_end == -1:
            crawl_job_end = len(api_content)
        crawl_job_func = api_content[crawl_job_start:crawl_job_end]

        # Find process_llm_extraction
        llm_extract_start = api_content.find('async def process_llm_extraction')
        llm_extract_end = api_content.find('\nasync def ', llm_extract_start + 1)
        if llm_extract_end == -1:
            llm_extract_end = len(api_content)
        llm_extract_func = api_content[llm_extract_start:llm_extract_end]

        print("Checking pattern consistency...")

        # Both should initialize WebhookDeliveryService
        crawl_has_service = 'webhook_service = WebhookDeliveryService(config)' in crawl_job_func
        llm_has_service = 'webhook_service = WebhookDeliveryService(config)' in llm_extract_func

        if crawl_has_service and llm_has_service:
            print("✅ Both initialize WebhookDeliveryService")
        else:
            print(f"❌ Service initialization mismatch (crawl: {crawl_has_service}, llm: {llm_has_service})")
            return False

        # Both should call notify_job_completion on success
        crawl_notifies_success = 'status="completed"' in crawl_job_func and 'notify_job_completion' in crawl_job_func
        llm_notifies_success = 'status="completed"' in llm_extract_func and 'notify_job_completion' in llm_extract_func

        if crawl_notifies_success and llm_notifies_success:
            print("✅ Both notify on success")
        else:
            print(f"❌ Success notification mismatch (crawl: {crawl_notifies_success}, llm: {llm_notifies_success})")
            return False

        # Both should call notify_job_completion on failure
        crawl_notifies_failure = 'status="failed"' in crawl_job_func and 'error=' in crawl_job_func
        llm_notifies_failure = 'status="failed"' in llm_extract_func and 'error=' in llm_extract_func

        if crawl_notifies_failure and llm_notifies_failure:
            print("✅ Both notify on failure")
        else:
            print(f"❌ Failure notification mismatch (crawl: {crawl_notifies_failure}, llm: {llm_notifies_failure})")
            return False

        print("✅ /llm/job follows the same pattern as /crawl/job")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False