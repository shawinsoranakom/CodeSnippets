def process_all_active_configs_v2(
    openai_api_key: str,
    tracking_db_path: Optional[str] = None,
    podcasts_db_path: Optional[str] = None,
    tasks_db_path: Optional[str] = None,
    output_dir: str = PODCAST_ASSETS_DIR,
    debug: bool = False,
) -> List[Dict[str, Any]]:
    if tracking_db_path is None:
        tracking_db_path = get_tracking_db_path()
    if podcasts_db_path is None:
        podcasts_db_path = get_podcasts_db_path()
    if tasks_db_path is None:
        tasks_db_path = get_tasks_db_path()
    configs = get_all_podcast_configs(tasks_db_path, active_only=True)
    if not configs:
        print("WARNING: No active podcast configurations found")
        return [{"error": "No active podcast configurations found"}]
    results = []
    total_configs = len(configs)
    print(f"Processing {total_configs} active podcast configurations with enhanced pipeline...")
    for i, config in enumerate(configs, 1):
        config_id = config["id"]
        config_name = config["name"]
        print(f"\n[{i}/{total_configs}] Processing podcast configuration {config_id}: {config_name}")
        try:
            result = generate_podcast_from_config_v2(
                config_id=config_id,
                openai_api_key=openai_api_key,
                tracking_db_path=tracking_db_path,
                podcasts_db_path=podcasts_db_path,
                tasks_db_path=tasks_db_path,
                output_dir=output_dir,
                debug=debug,
            )
            result["config_id"] = config_id
            result["config_name"] = config_name
            results.append(result)
            if "error" not in result:
                stats = result.get("processing_stats", {})
                print(f"Success - Podcast ID: {result.get('podcast_id', 'Unknown')}")
                print(f"Sources: {stats.get('confirmed_results', 0)} articles processed")
                print(f"Images: {stats.get('images_generated', 0)} generated")
                print(f"Audio: {'Yes' if stats.get('audio_generated') else 'No'}")
            else:
                print(f"Failed: {result['error']}")
        except Exception as e:
            print(f"ERROR: Error generating podcast for config {config_id}: {e}")
            results.append({"config_id": config_id, "config_name": config_name, "error": str(e)})
    return results