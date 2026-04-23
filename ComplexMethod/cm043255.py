async def select_links_for_expansion(
        self, 
        candidate_links: List[Link], 
        gaps: List[Tuple[Any, float]], 
        kb_embeddings: Any
    ) -> List[Tuple[Link, float]]:
        """Select links that most efficiently fill the gaps"""
        from .utils import cosine_distance, cosine_similarity, get_text_embeddings
        import numpy as np
        import hashlib

        scored_links = []

        # Prepare for embedding - separate cached vs uncached
        links_to_embed = []
        texts_to_embed = []
        link_embeddings_map = {}

        for link in candidate_links:
            # Extract text from link
            link_text = ' '.join(filter(None, [
                link.text or '',
                link.title or '',
                link.meta.get('description', '') if hasattr(link, 'meta') and link.meta else '',
                link.head_data.get('meta', {}).get('description', '') if link.head_data else ''
            ]))

            if not link_text.strip():
                continue

            # Create cache key from URL + text content
            cache_key = hashlib.md5(f"{link.href}:{link_text}".encode()).hexdigest()

            # Check cache
            if cache_key in self._link_embedding_cache:
                link_embeddings_map[link.href] = self._link_embedding_cache[cache_key]
            else:
                links_to_embed.append(link)
                texts_to_embed.append(link_text)

        # Batch embed only uncached links
        if texts_to_embed:
            embedding_llm_config = {
                'provider': 'openai/text-embedding-3-small',
                'api_token': os.getenv('OPENAI_API_KEY')
            }
            new_embeddings = await get_text_embeddings(texts_to_embed, embedding_llm_config, self.embedding_model)

            # Cache the new embeddings
            for link, text, embedding in zip(links_to_embed, texts_to_embed, new_embeddings):
                cache_key = hashlib.md5(f"{link.href}:{text}".encode()).hexdigest()
                self._link_embedding_cache[cache_key] = embedding
                link_embeddings_map[link.href] = embedding

        # Get coverage radius from config
        coverage_radius = self.config.embedding_coverage_radius if hasattr(self, 'config') else 0.2

        # Score each link
        for link in candidate_links:
            if link.href not in link_embeddings_map:
                continue  # Skip links without embeddings

            link_embedding = link_embeddings_map[link.href]

            if not gaps:
                score = 0.0
            else:
                # Calculate how many gaps this link helps with
                gaps_helped = 0
                total_improvement = 0

                for gap_point, gap_distance in gaps:
                    # Only consider gaps that actually need filling (outside coverage radius)
                    if gap_distance > coverage_radius:
                        new_distance = cosine_distance(link_embedding, gap_point)
                        if new_distance < gap_distance:
                            # This link helps this gap
                            improvement = gap_distance - new_distance
                            # Scale improvement - moving from 0.5 to 0.3 is valuable
                            scaled_improvement = improvement * 2  # Amplify the signal
                            total_improvement += scaled_improvement
                            gaps_helped += 1

                # Average improvement per gap that needs help
                gaps_needing_help = sum(1 for _, d in gaps if d > coverage_radius)
                if gaps_needing_help > 0:
                    gap_reduction_score = total_improvement / gaps_needing_help
                else:
                    gap_reduction_score = 0

                # Check overlap with existing KB (vectorized)
                if kb_embeddings is not None and len(kb_embeddings) > 0:
                    # Normalize embeddings
                    link_norm = link_embedding / np.linalg.norm(link_embedding)
                    kb_norm = kb_embeddings / np.linalg.norm(kb_embeddings, axis=1, keepdims=True)

                    # Compute all similarities at once
                    similarities = np.dot(kb_norm, link_norm)
                    max_similarity = np.max(similarities)

                    # Only penalize if very similar (above threshold)
                    overlap_threshold = self.config.embedding_overlap_threshold if hasattr(self, 'config') else 0.85
                    if max_similarity > overlap_threshold:
                        overlap_penalty = (max_similarity - overlap_threshold) * 2  # 0 to 0.3 range
                    else:
                        overlap_penalty = 0
                else:
                    overlap_penalty = 0

                # Final score - emphasize gap reduction
                score = gap_reduction_score * (1 - overlap_penalty)

                # Add contextual score boost if available
                if hasattr(link, 'contextual_score') and link.contextual_score:
                    score = score * 0.8 + link.contextual_score * 0.2

            scored_links.append((link, score))

        return sorted(scored_links, key=lambda x: x[1], reverse=True)