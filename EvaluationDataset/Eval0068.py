def warp(
    image: np.ndarray, horizontal_flow: np.ndarray, vertical_flow: np.ndarray
) -> np.ndarray:

    flow = np.stack((horizontal_flow, vertical_flow), 2)


    grid = np.stack(
        np.meshgrid(np.arange(0, image.shape[1]), np.arange(0, image.shape[0])), 2
    )
    grid = np.round(grid - flow).astype(np.int32)

    invalid = (grid < 0) | (grid >= np.array([image.shape[1], image.shape[0]]))
    grid[invalid] = 0

    warped = image[grid[:, :, 1], grid[:, :, 0]]

    warped[invalid[:, :, 0] | invalid[:, :, 1]] = 0

    return warped
