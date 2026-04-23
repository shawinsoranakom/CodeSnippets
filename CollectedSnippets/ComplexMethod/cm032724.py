def _process_video(self, video_bytes, filename):
        from google import genai
        from google.genai import types

        video_size_mb = len(video_bytes) / (1024 * 1024)
        client = self.client if hasattr(self, "client") else genai.Client(api_key=self.api_key)
        logging.info(f"[GeminiCV] _process_video called: filename={filename} size_mb={video_size_mb:.2f}")

        tmp_path = None
        try:
            if video_size_mb <= 20:
                response = client.models.generate_content(
                    model="models/gemini-2.5-flash",
                    contents=types.Content(parts=[types.Part(inline_data=types.Blob(data=video_bytes, mime_type="video/mp4")), types.Part(text="Please summarize the video in proper sentences.")]),
                )
            else:
                logging.info(f"Video size {video_size_mb:.2f}MB exceeds 20MB. Using Files API...")
                video_suffix = Path(filename).suffix or ".mp4"
                with tempfile.NamedTemporaryFile(delete=False, suffix=video_suffix) as tmp:
                    tmp.write(video_bytes)
                    tmp_path = Path(tmp.name)
                uploaded_file = client.files.upload(file=tmp_path)

                response = client.models.generate_content(model="gemini-2.5-flash", contents=[uploaded_file, "Please summarize this video in proper sentences."])

            summary = response.text or ""
            logging.info(f"[GeminiCV] Video summarized: {summary[:32]}...")
            return summary, num_tokens_from_string(summary)
        except Exception as e:
            logging.warning(f"[GeminiCV] Video processing failed: {e}")
            raise
        finally:
            if tmp_path and tmp_path.exists():
                tmp_path.unlink()