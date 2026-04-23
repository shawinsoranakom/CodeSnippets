def frame_faces_to_alignment(media: FrameFaces) -> list[PNGAlignments]:
    """Convert the faces in a FrameFaces object into a list of dictionaries (one for each face)
    for serializing into image headers and alignments files"""
    if not media:
        return []
    assert media.landmarks is not None
    assert media.landmarks.shape[0] == len(media)
    assert all(m.masks.shape[0] == m.matrices.shape[0] == len(media) for m in media.masks.values())
    assert all(i.shape[0] == len(media) for i in media.identities.values())

    masks = {}
    for k, v in media.masks.items():
        scales = np.hypot(v.matrices[..., 0, 0], v.matrices[..., 1, 0])  # Always same x/y scaling
        interpolators = np.where(scales > 1.0, cv2.INTER_LINEAR, cv2.INTER_AREA)
        store_masks = v.masks
        mats = v.matrices
        if v.storage_size != v.masks.shape[1]:
            store_masks = batch_resize(v.masks[..., None], v.storage_size)[..., 0]
            mats = mats.copy()
            mats[:, :2] *= v.storage_size / v.masks.shape[1]
        masks[k] = {"mask": [compress(m.tobytes()) for m in store_masks],
                    "mats": mats.tolist(),
                    "interpolators": interpolators.tolist(),
                    "size": v.storage_size,
                    "centering": v.centering}

    return [PNGAlignments(x=int(bbox[0]),
                          y=int(bbox[1]),
                          w=int(bbox[2] - bbox[0]),
                          h=int(bbox[3] - bbox[1]),
                          landmarks_xy=lms,
                          mask={k: MaskAlignmentsFile(mask=m["mask"][idx],
                                                      affine_matrix=m["mats"][idx],
                                                      interpolator=int(m["interpolators"][idx]),
                                                      stored_size=m["size"],
                                                      stored_centering=m["centering"])
                                for k, m in masks.items()},
                          identity={k: i[idx].tolist() for k, i in media.identities.items()})
            for idx, (bbox, lms) in enumerate(zip(media.bboxes, media.landmarks.tolist()))]