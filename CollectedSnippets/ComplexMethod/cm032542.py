def wait_for_parsing_completion(auth, dataset_id, document_id=None):
    """
    Wait for document parsing to complete.

    Args:
        auth: Authentication object
        dataset_id: Dataset ID
        document_id: Optional specific document ID to wait for

    Returns:
        bool: True if parsing is complete, False otherwise
    """
    res = list_documents(auth, dataset_id)
    docs = res["data"]["docs"]

    if document_id is None:
        # Wait for all documents to complete
        for doc in docs:
            status = doc.get("run", "UNKNOWN")
            if status != "DONE":
                # print(f"[DEBUG] Document {doc.get('name', 'unknown')} status: {status}, progress: {doc.get('progress', 0)}%, msg: {doc.get('progress_msg', '')}")
                return False
        return True
    else:
        # Wait for specific document
        for doc in docs:
            if doc["id"] == document_id:
                status = doc.get("run", "UNKNOWN")
                # print(f"[DEBUG] Document {doc.get('name', 'unknown')} status: {status}, progress: {doc.get('progress', 0)}%, msg: {doc.get('progress_msg', '')}")
                if status == "DONE":
                    return True
                elif status == "FAILED":
                    pytest.fail(f"Document parsing failed: {doc}")
                    return False
        return False