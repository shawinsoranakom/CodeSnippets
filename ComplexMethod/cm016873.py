def voxel_to_mesh_surfnet(voxels, threshold=0.5, device=None):
    if device is None:
        device = torch.device("cpu")
    voxels = voxels.to(device)

    D, H, W = voxels.shape

    padded = torch.nn.functional.pad(voxels, (1, 1, 1, 1, 1, 1), 'constant', 0)
    z, y, x = torch.meshgrid(
        torch.arange(D, device=device),
        torch.arange(H, device=device),
        torch.arange(W, device=device),
        indexing='ij'
    )
    cell_positions = torch.stack([z.flatten(), y.flatten(), x.flatten()], dim=1)

    corner_offsets = torch.tensor([
        [0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0],
        [0, 0, 1], [1, 0, 1], [0, 1, 1], [1, 1, 1]
    ], device=device)

    pos = cell_positions.unsqueeze(1) + corner_offsets.unsqueeze(0)
    z_idx, y_idx, x_idx = pos.unbind(-1)
    corner_values = padded[z_idx, y_idx, x_idx]

    corner_signs = corner_values > threshold
    has_inside = torch.any(corner_signs, dim=1)
    has_outside = torch.any(~corner_signs, dim=1)
    contains_surface = has_inside & has_outside

    active_cells = cell_positions[contains_surface]
    active_signs = corner_signs[contains_surface]
    active_values = corner_values[contains_surface]

    if active_cells.shape[0] == 0:
        return torch.zeros((0, 3), device=device), torch.zeros((0, 3), dtype=torch.long, device=device)

    edges = torch.tensor([
        [0, 1], [0, 2], [0, 4], [1, 3],
        [1, 5], [2, 3], [2, 6], [3, 7],
        [4, 5], [4, 6], [5, 7], [6, 7]
    ], device=device)

    cell_vertices = {}
    progress = comfy.utils.ProgressBar(100)

    for edge_idx, (e1, e2) in enumerate(edges):
        progress.update(1)
        crossing = active_signs[:, e1] != active_signs[:, e2]
        if not crossing.any():
            continue

        cell_indices = torch.nonzero(crossing, as_tuple=True)[0]

        v1 = active_values[cell_indices, e1]
        v2 = active_values[cell_indices, e2]

        t = torch.zeros_like(v1, device=device)
        denom = v2 - v1
        valid = denom != 0
        t[valid] = (threshold - v1[valid]) / denom[valid]
        t[~valid] = 0.5

        p1 = corner_offsets[e1].float()
        p2 = corner_offsets[e2].float()

        intersection = p1.unsqueeze(0) + t.unsqueeze(1) * (p2.unsqueeze(0) - p1.unsqueeze(0))

        for i, point in zip(cell_indices.tolist(), intersection):
            if i not in cell_vertices:
                cell_vertices[i] = []
            cell_vertices[i].append(point)

    # Calculate the final vertices as the average of intersection points for each cell
    vertices = []
    vertex_lookup = {}

    vert_progress_mod = round(len(cell_vertices)/50)

    for i, points in cell_vertices.items():
        if not i % vert_progress_mod:
            progress.update(1)

        if points:
            vertex = torch.stack(points).mean(dim=0)
            vertex = vertex + active_cells[i].float()
            vertex_lookup[tuple(active_cells[i].tolist())] = len(vertices)
            vertices.append(vertex)

    if not vertices:
        return torch.zeros((0, 3), device=device), torch.zeros((0, 3), dtype=torch.long, device=device)

    final_vertices = torch.stack(vertices)

    inside_corners_mask = active_signs
    outside_corners_mask = ~active_signs

    inside_counts = inside_corners_mask.sum(dim=1, keepdim=True).float()
    outside_counts = outside_corners_mask.sum(dim=1, keepdim=True).float()

    inside_pos = torch.zeros((active_cells.shape[0], 3), device=device)
    outside_pos = torch.zeros((active_cells.shape[0], 3), device=device)

    for i in range(8):
        mask_inside = inside_corners_mask[:, i].unsqueeze(1)
        mask_outside = outside_corners_mask[:, i].unsqueeze(1)
        inside_pos += corner_offsets[i].float().unsqueeze(0) * mask_inside
        outside_pos += corner_offsets[i].float().unsqueeze(0) * mask_outside

    inside_pos /= inside_counts
    outside_pos /= outside_counts
    gradients = inside_pos - outside_pos

    pos_dirs = torch.tensor([
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1]
    ], device=device)

    cross_products = [
        torch.linalg.cross(pos_dirs[i].float(), pos_dirs[j].float())
        for i in range(3) for j in range(i+1, 3)
    ]

    faces = []
    all_keys = set(vertex_lookup.keys())

    face_progress_mod = round(len(active_cells)/38*3)

    for pair_idx, (i, j) in enumerate([(0,1), (0,2), (1,2)]):
        dir_i = pos_dirs[i]
        dir_j = pos_dirs[j]
        cross_product = cross_products[pair_idx]

        ni_positions = active_cells + dir_i
        nj_positions = active_cells + dir_j
        diag_positions = active_cells + dir_i + dir_j

        alignments = torch.matmul(gradients, cross_product)

        valid_quads = []
        quad_indices = []

        for idx, active_cell in enumerate(active_cells):
            if not idx % face_progress_mod:
                progress.update(1)
            cell_key = tuple(active_cell.tolist())
            ni_key = tuple(ni_positions[idx].tolist())
            nj_key = tuple(nj_positions[idx].tolist())
            diag_key = tuple(diag_positions[idx].tolist())

            if cell_key in all_keys and ni_key in all_keys and nj_key in all_keys and diag_key in all_keys:
                v0 = vertex_lookup[cell_key]
                v1 = vertex_lookup[ni_key]
                v2 = vertex_lookup[nj_key]
                v3 = vertex_lookup[diag_key]

                valid_quads.append((v0, v1, v2, v3))
                quad_indices.append(idx)

        for q_idx, (v0, v1, v2, v3) in enumerate(valid_quads):
            cell_idx = quad_indices[q_idx]
            if alignments[cell_idx] > 0:
                faces.append(torch.tensor([v0, v1, v3], device=device, dtype=torch.long))
                faces.append(torch.tensor([v0, v3, v2], device=device, dtype=torch.long))
            else:
                faces.append(torch.tensor([v0, v3, v1], device=device, dtype=torch.long))
                faces.append(torch.tensor([v0, v2, v3], device=device, dtype=torch.long))

    if faces:
        faces = torch.stack(faces)
    else:
        faces = torch.zeros((0, 3), dtype=torch.long, device=device)

    v_min = 0
    v_max = max(D, H, W)

    final_vertices = final_vertices - (v_min + v_max) / 2

    scale = (v_max - v_min) / 2
    if scale > 0:
        final_vertices = final_vertices / scale

    final_vertices = torch.fliplr(final_vertices)

    return final_vertices, faces