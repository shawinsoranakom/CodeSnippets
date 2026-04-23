def generate_podcast_from_prompt_v2(
    prompt: str,
    openai_api_key: str,
    tracking_db_path: Optional[str] = None,
    podcasts_db_path: Optional[str] = None,
    output_dir: str = PODCAST_ASSETS_DIR,
    tts_engine: str = "kokoro",
    language_code: str = "en",
    podcast_script_prompt: Optional[str] = None,
    image_prompt: Optional[str] = None,
    debug: bool = False,
) -> Dict[str, Any]:
    if tracking_db_path is None:
        tracking_db_path = get_tracking_db_path()
    if podcasts_db_path is None:
        podcasts_db_path = get_podcasts_db_path()
    os.makedirs(output_dir, exist_ok=True)
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    print(f"Starting enhanced podcast generation for prompt: {prompt}")
    try:
        search_results = search_agent_run(prompt)
        if not search_results:
            print(f"WARNING: No search results found for prompt: {prompt}")
            return {"error": "No search results found"}
        print(f"Found {len(search_results)} search results")
        if debug:
            print("Search results:", json.dumps(search_results[:2], indent=2))
    except Exception as e:
        print(f"ERROR: Search agent failed: {e}")
        return {"error": f"Search agent failed: {str(e)}"}
    try:
        scraped_results = scrape_agent_run(prompt, search_results)
        if not scraped_results:
            print("WARNING: No content could be scraped")
            return {"error": "No content could be scraped"}
        confirmed_results = []
        for result in scraped_results:
            if result.get("full_text") and len(result["full_text"].strip()) > 100:
                result["confirmed"] = True
                confirmed_results.append(result)
        if not confirmed_results:
            print("WARNING: No high-quality content available after scraping")
            return {"error": "No high-quality content available"}
        print(f"Successfully scraped {len(confirmed_results)} high-quality articles")
        if debug:
            print("Sample scraped content:", confirmed_results[0].get("full_text", "")[:200])
    except Exception as e:
        print(f"ERROR: Scrape agent failed: {e}")
        return {"error": f"Scrape agent failed: {str(e)}"}
    try:
        language_name = get_language_name(language_code)
        podcast_data = script_agent_run(query=prompt, search_results=confirmed_results, language_name=language_name)
        if not podcast_data or not isinstance(podcast_data, dict):
            print("ERROR: Failed to generate podcast script")
            return {"error": "Failed to generate podcast script"}
        if not podcast_data.get("sections"):
            print("ERROR: Generated podcast script is missing required sections")
            return {"error": "Invalid podcast script structure"}
        print(f"Generated script with {len(podcast_data['sections'])} sections")
        if debug:
            print("Script title:", podcast_data.get("title", "No title"))
    except Exception as e:
        print(f"ERROR: Script agent failed: {e}")
        return {"error": f"Script agent failed: {str(e)}"}
    banner_filenames = []
    banner_url = None
    try:
        image_query = image_prompt if image_prompt else prompt
        image_result = image_generation_agent_run(image_query, podcast_data)
        if image_result and image_result.get("banner_images"):
            banner_filenames = image_result["banner_images"]
            banner_url = image_result.get("banner_url")
            print(f"Generated {len(banner_filenames)} banner images")
        else:
            print("WARNING: No images were generated")
    except Exception as e:
        print(f"ERROR: Image generation failed: {e}")
    audio_filename = None
    full_audio_path = None
    try:
        audio_format = convert_script_to_audio_format(podcast_data)
        audio_filename = f"podcast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        audio_path = os.path.join(output_dir, "audio", audio_filename)

        class DictPodcastScript:
            def __init__(self, entries):
                self.entries = entries

            def __iter__(self):
                return iter(self.entries)

        script_obj = DictPodcastScript(audio_format["entries"])
        full_audio_path = generate_podcast_audio(
            script=script_obj,
            output_path=audio_path,
            tts_engine=tts_engine,
            language_code=language_code,
        )
        if full_audio_path:
            print(f"Generated podcast audio: {full_audio_path}")
        else:
            print("ERROR: Failed to generate audio")
            audio_filename = None
    except Exception as e:
        print(f"ERROR: Error generating audio: {e}")
        import traceback

        traceback.print_exc()
        audio_filename = None
    try:
        session_state = {
            "generated_script": podcast_data,
            "banner_url": banner_url,
            "banner_images": banner_filenames,
            "audio_url": full_audio_path,
            "tts_engine": tts_engine,
            "selected_language": {"code": language_code, "name": get_language_name(language_code)},
            "podcast_info": {"topic": prompt},
        }
        success, message, podcast_id = _save_podcast_to_database_sync(session_state)
        if success:
            print(f"Stored podcast data with ID: {podcast_id}")
        else:
            print(f"ERROR: Failed to save to database: {message}")
            podcast_id = 0
    except Exception as e:
        print(f"ERROR: Error storing podcast data: {e}")
        podcast_id = 0
    if audio_filename:
        frontend_audio_path = os.path.join(output_dir, audio_filename).replace("\\", "/")
    else:
        frontend_audio_path = None
    if banner_url:
        frontend_banner_path = banner_url.replace("\\", "/")
    else:
        frontend_banner_path = None
    return {
        "podcast_id": podcast_id,
        "title": podcast_data.get("title", "Podcast"),
        "audio_path": frontend_audio_path,
        "banner_path": frontend_banner_path,
        "banner_images": banner_filenames,
        "script": podcast_data,
        "tts_engine": tts_engine,
        "language": language_code,
        "sources_count": len(confirmed_results),
        "processing_stats": {
            "search_results": len(search_results),
            "scraped_results": len(scraped_results),
            "confirmed_results": len(confirmed_results),
            "images_generated": len(banner_filenames),
            "audio_generated": bool(audio_filename),
        },
    }