def toggle_podcast_generated(session_state: dict, status: bool = False) -> str:
    """
    Toggle the podcast_generated flag.
    When set to true, this indicates the podcast creation process is complete and
    the UI should show the final presentation view with all components.
    If status is True, also saves the podcast to the podcasts database.
    """
    if status:
        session_state["podcast_generated"] = status
        session_state["stage"] = "complete" if status else session_state.get("stage")
        if status:
            try:
                success, message, podcast_id = _save_podcast_to_database_sync(session_state)
                if success and podcast_id:
                    session_state["podcast_id"] = podcast_id
                    return f"Podcast generated and saved to database with ID: {podcast_id}. You can now access it from the Podcasts section."
                else:
                    return f"Podcast generated, but there was an issue with saving: {message}"
            except Exception as e:
                print(f"Error saving podcast to database: {e}")
                return f"Podcast generated, but there was an error saving it to the database: {str(e)}"
    else:
        session_state["podcast_generated"] = status
        session_state["stage"] = "complete" if status else session_state.get("stage")
    return f"Podcast generated status changed to: {status}"