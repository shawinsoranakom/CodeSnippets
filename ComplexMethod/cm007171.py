def validate_video_file(self, filepath: str) -> tuple[bool, str]:
        """Validate video file using ffprobe.

        Returns (is_valid, error_message).
        """
        # Ensure filepath is a string and doesn't contain shell metacharacters
        if not isinstance(filepath, str) or any(c in filepath for c in ";&|`$(){}[]<>*?!#~"):
            return False, "Invalid filepath"

        try:
            cmd = [
                "ffprobe",
                "-loglevel",
                "error",
                "-show_entries",
                "stream=codec_type,codec_name",
                "-of",
                "default=nw=1",
                "-print_format",
                "json",
                "-show_format",
                filepath,
            ]

            # Use subprocess with a list of arguments to avoid shell injection
            # We need to skip the S603 warning here as we're taking proper precautions
            # with input validation and using shell=False
            result = subprocess.run(  # noqa: S603
                cmd,
                capture_output=True,
                text=True,
                check=False,
                shell=False,  # Explicitly set shell=False for security
            )

            if result.returncode != 0:
                return False, f"FFprobe error: {result.stderr}"

            probe_data = json.loads(result.stdout)

            has_video = any(stream.get("codec_type") == "video" for stream in probe_data.get("streams", []))

            if not has_video:
                return False, "No video stream found in file"

            self.log(f"Video validation successful: {json.dumps(probe_data, indent=2)}")
        except subprocess.SubprocessError as e:
            return False, f"FFprobe process error: {e!s}"
        except json.JSONDecodeError as e:
            return False, f"FFprobe output parsing error: {e!s}"
        except (ValueError, OSError) as e:
            return False, f"Validation error: {e!s}"
        else:
            return True, ""