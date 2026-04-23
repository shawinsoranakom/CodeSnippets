def process_streaming(generator: Iterator[Mapping[str, Any]]) -> None:
    progress_bars = {}
    queue = deque()  # type: ignore

    def create_progress_bar(dgt: str, total: int) -> Any:
        return tqdm(
            total=total, desc=f"Pulling model {dgt[7:17]}...", unit="B", unit_scale=True
        )

    current_digest = None

    for chunk in generator:
        digest = chunk.get("digest")
        completed_size = chunk.get("completed", 0)
        total_size = chunk.get("total")

        if digest and total_size is not None:
            if digest not in progress_bars and completed_size > 0:
                progress_bars[digest] = create_progress_bar(digest, total=total_size)
                if current_digest is None:
                    current_digest = digest
                else:
                    queue.append(digest)

            if digest in progress_bars:
                progress_bar = progress_bars[digest]
                progress = completed_size - progress_bar.n
                if completed_size > 0 and total_size >= progress != progress_bar.n:
                    if digest == current_digest:
                        progress_bar.update(progress)
                        if progress_bar.n >= total_size:
                            progress_bar.close()
                            current_digest = queue.popleft() if queue else None
                    else:
                        # Store progress for later update
                        progress_bars[digest].total = total_size
                        progress_bars[digest].n = completed_size

    # Close any remaining progress bars at the end
    for progress_bar in progress_bars.values():
        progress_bar.close()