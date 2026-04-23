def delete_asset_reference(
    reference_id: str,
    owner_id: str,
    delete_content_if_orphan: bool = True,
) -> bool:
    with create_session() as session:
        if not delete_content_if_orphan:
            # Soft delete: mark the reference as deleted but keep everything
            deleted = soft_delete_reference_by_id(
                session, reference_id=reference_id, owner_id=owner_id
            )
            session.commit()
            return deleted

        ref_row = get_reference_by_id(session, reference_id=reference_id)
        asset_id = ref_row.asset_id if ref_row else None
        file_path = ref_row.file_path if ref_row else None

        deleted = delete_reference_by_id(
            session, reference_id=reference_id, owner_id=owner_id
        )
        if not deleted:
            session.commit()
            return False

        if not asset_id:
            session.commit()
            return True

        still_exists = reference_exists_for_asset_id(session, asset_id=asset_id)
        if still_exists:
            session.commit()
            return True

        # Orphaned asset - gather ALL file paths (including
        # soft-deleted / missing refs) so their on-disk files get cleaned up.
        file_paths = list_all_file_paths_by_asset_id(session, asset_id=asset_id)
        # Also include the just-deleted file path
        if file_path:
            file_paths.append(file_path)

        asset_row = session.get(Asset, asset_id)
        if asset_row is not None:
            session.delete(asset_row)

        session.commit()

        # Delete files after commit
        for p in file_paths:
            with contextlib.suppress(Exception):
                if p and os.path.isfile(p):
                    os.remove(p)

    return True