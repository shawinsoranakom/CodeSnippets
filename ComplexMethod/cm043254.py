def _calculate_authority(self, link: Link) -> float:
        """Simple authority score based on URL structure and link attributes"""
        score = 0.5  # Base score

        if not link.href:
            return 0.0

        url = link.href.lower()

        # Positive indicators
        if '/docs/' in url or '/documentation/' in url:
            score += 0.2
        if '/api/' in url or '/reference/' in url:
            score += 0.2
        if '/guide/' in url or '/tutorial/' in url:
            score += 0.1

        # Check for file extensions
        if url.endswith('.pdf'):
            score += 0.1
        elif url.endswith(('.jpg', '.png', '.gif')):
            score -= 0.3  # Reduce score for images

        # Use intrinsic score if available
        if link.intrinsic_score is not None:
            score = 0.7 * score + 0.3 * link.intrinsic_score

        return min(score, 1.0)