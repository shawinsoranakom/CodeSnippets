async def process_record(session, semaphore, record):
        """Process single image record with async session."""
        async with semaphore:
            split, original_name = record["split"], record["file"]
            annotations = record.get("annotations", {})

            if is_classification:
                # Classification: place image in {split}/{class_name}/ folder
                class_ids = annotations.get("classification", [])
                class_id = class_ids[0] if class_ids else 0
                class_name = class_names.get(class_id, str(class_id))
                image_path = dataset_dir / split / class_name / original_name
            else:
                # Detection: write label file and place image in images/{split}/
                image_path = dataset_dir / "images" / split / original_name
                label_path = dataset_dir / "labels" / split / f"{Path(original_name).stem}.txt"
                lines_to_write = []
                for key in annotations.keys():
                    lines_to_write = [" ".join(map(str, item)) for item in annotations[key]]
                    break
                label_path.write_text("\n".join(lines_to_write) + "\n" if lines_to_write else "")

            # Reuse existing image from another split dir (avoids redownload on resplit) or download
            if not image_path.exists():
                if _reuse:
                    for s in ("train", "val", "test"):
                        if s == split:
                            continue
                        candidate = (
                            (dataset_dir / s / class_name / original_name)
                            if is_classification
                            else (dataset_dir / "images" / s / original_name)
                        )
                        if candidate.exists():
                            image_path.parent.mkdir(parents=True, exist_ok=True)
                            candidate.rename(image_path)
                            break
                if not image_path.exists() and (http_url := record.get("url")):
                    image_path.parent.mkdir(parents=True, exist_ok=True)
                    # Retry with exponential backoff (3 attempts: 1s, 2s delays before the final attempt)
                    for attempt in range(3):
                        error = None
                        try:
                            async with session.get(http_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                                response.raise_for_status()
                                image_path.write_bytes(await response.read())
                            return True
                        except aiohttp.ClientResponseError as e:
                            error = e
                            if e.status not in {408, 429} and e.status < 500:
                                LOGGER.warning(f"Failed to download {http_url}: {e}")
                                return False
                        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                            error = e
                        except Exception as e:  # OSError, disk full, permissions — not transient, don't retry
                            LOGGER.warning(f"Failed to save {http_url}: {e}")
                            return False
                        if attempt < 2:  # Don't sleep after last attempt
                            await asyncio.sleep(2**attempt)  # 1s, 2s backoff
                        else:
                            LOGGER.warning(f"Failed to download {http_url} after 3 attempts: {error}")
                            return False
            return True