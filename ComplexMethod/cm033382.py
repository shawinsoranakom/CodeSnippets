async def delete_datasets(tenant_id: str, ids: list = None, delete_all: bool = False):
    """
    Delete datasets.

    :param tenant_id: tenant ID
    :param ids: list of dataset IDs
    :param delete_all: whether to delete all datasets of the tenant (if ids is not provided)
    :return: (success, result) or (success, error_message)
    """
    kb_id_instance_pairs = []
    if not ids:
        if not delete_all:
            return True, {"success_count": 0}
        else:
            ids = [kb.id for kb in KnowledgebaseService.query(tenant_id=tenant_id)]

    error_kb_ids = []
    for kb_id in ids:
        kb = KnowledgebaseService.get_or_none(id=kb_id, tenant_id=tenant_id)
        if kb is None:
            error_kb_ids.append(kb_id)
            continue
        kb_id_instance_pairs.append((kb_id, kb))
    if len(error_kb_ids) > 0:
        return False, f"""User '{tenant_id}' lacks permission for datasets: '{", ".join(error_kb_ids)}'"""

    errors = []
    success_count = 0
    for kb_id, kb in kb_id_instance_pairs:
        for doc in DocumentService.query(kb_id=kb_id):
            if not DocumentService.remove_document(doc, tenant_id):
                errors.append(f"Remove document '{doc.id}' error for dataset '{kb_id}'")
                continue
            f2d = File2DocumentService.get_by_document_id(doc.id)
            FileService.filter_delete(
                [
                    File.source_type == FileSource.KNOWLEDGEBASE,
                    File.id == f2d[0].file_id,
                ]
            )
            File2DocumentService.delete_by_document_id(doc.id)
        FileService.filter_delete(
            [File.source_type == FileSource.KNOWLEDGEBASE, File.type == "folder", File.name == kb.name])

        # Drop index for this dataset
        try:
            from rag.nlp import search
            idxnm = search.index_name(kb.tenant_id)
            settings.docStoreConn.delete_idx(idxnm, kb_id)
        except Exception as e:
            errors.append(f"Failed to drop index for dataset {kb_id}: {e}")

        if not KnowledgebaseService.delete_by_id(kb_id):
            errors.append(f"Delete dataset error for {kb_id}")
            continue
        success_count += 1

    if not errors:
        return True, {"success_count": success_count}

    error_message = f"Successfully deleted {success_count} datasets, {len(errors)} failed. Details: {'; '.join(errors)[:128]}..."
    if success_count == 0:
        return False, error_message

    return True, {"success_count": success_count, "errors": errors[:5]}