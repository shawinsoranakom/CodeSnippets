def parse(self, content: str) -> dict[str, str]:
        checksums = {}
        lines = content.strip().split("\n")

        current_file = None
        checksum_parts = []

        for line in lines:
            if ":" in line and not line.startswith(" "):
                # New file entry
                if current_file and checksum_parts:
                    # Save previous file's checksum
                    full_checksum = "".join(checksum_parts).replace(" ", "").lower()
                    if re.match(r"^[a-fA-F0-9]+$", full_checksum):
                        checksums[current_file] = full_checksum

                # Start new file
                parts = line.split(":", 1)
                current_file = parts[0].strip()
                checksum_part = parts[1].strip()
                checksum_parts = [checksum_part]
            elif line.strip() and current_file:
                # Continuation of checksum
                checksum_parts.append(line.strip())

        # Don't forget the last file
        if current_file and checksum_parts:
            full_checksum = "".join(checksum_parts).replace(" ", "").lower()
            if re.match(r"^[a-fA-F0-9]+$", full_checksum):
                checksums[current_file] = full_checksum

        return checksums