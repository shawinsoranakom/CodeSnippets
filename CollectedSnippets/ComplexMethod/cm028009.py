def show_retrieval_info(client, raw_response, agent_id: str) -> None:
    try:
        if not raw_response:
            st.info("No retrieval info available.")
            return
        message_id = getattr(raw_response, "message_id", None)
        retrieval_contents = getattr(raw_response, "retrieval_contents", [])
        if not message_id or not retrieval_contents:
            st.info("No retrieval metadata returned.")
            return
        first_content_id = getattr(retrieval_contents[0], "content_id", None)
        if not first_content_id:
            st.info("Missing content_id in retrieval metadata.")
            return
        ret_result = client.agents.query.retrieval_info(message_id=message_id, agent_id=agent_id, content_ids=[first_content_id])
        metadatas = getattr(ret_result, "content_metadatas", [])
        if not metadatas:
            st.info("No content metadatas found.")
            return
        page_img_b64 = getattr(metadatas[0], "page_img", None)
        if not page_img_b64:
            st.info("No page image provided in metadata.")
            return
        import base64
        img_bytes = base64.b64decode(page_img_b64)
        st.image(img_bytes, caption="Top Attribution Page", use_container_width=True)
        # Removed raw object rendering to keep UI clean
    except Exception as e:
        st.error(f"Failed to load retrieval info: {e}")