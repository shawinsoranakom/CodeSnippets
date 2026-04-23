def ingest_video(
        self,
        video_path: str,
        filename: str,
        fps: float = 1.0,
        on_progress=None,
    ) -> dict:
        """Ingest a video: extract frames, embed each, store in ChromaDB."""
        frames, duration, video_id = self.extract_frames(video_path, fps)

        if not frames:
            return {"error": "No frames extracted", "video_id": video_id}

        # Read all frame images
        frame_data = []
        for f in frames:
            with open(f["path"], "rb") as fh:
                frame_data.append((fh.read(), "image/jpeg"))

        # Embed in batches
        total = len(frame_data)
        embeddings = []
        batch_size = 6

        for i in range(0, total, batch_size):
            batch = frame_data[i:i + batch_size]
            parts = [types.Part.from_bytes(data=self._resize_image(data), mime_type="image/jpeg") for data, mime in batch]
            result = self.client.models.embed_content(
                model=EMBED_MODEL,
                contents=parts,
            )
            embeddings.extend([e.values for e in result.embeddings])
            if on_progress:
                on_progress(min(i + batch_size, total), total)

        # Store in ChromaDB
        ids = []
        metadatas = []
        documents = []

        for i, frame in enumerate(frames):
            frame_id = f"{video_id}_f{frame['frame_num']:04d}"
            ids.append(frame_id)
            metadatas.append({
                "video_id": video_id,
                "video_filename": filename,
                "timestamp": frame["timestamp"],
                "frame_num": frame["frame_num"],
                "frame_path": frame["path"],
                "total_frames": total,
                "duration": duration,
                "fps": fps,
            })
            documents.append(f"Frame {frame['frame_num']} at {frame['timestamp']:.1f}s from {filename}")

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        return {
            "video_id": video_id,
            "filename": filename,
            "duration": round(duration, 1),
            "frames_extracted": total,
            "fps": fps,
        }