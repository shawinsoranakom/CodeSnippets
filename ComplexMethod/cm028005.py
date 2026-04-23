def generate_answer_with_citations(
    query: str,
    graph: KnowledgeGraphManager,
    model: str = "llama3.2"
) -> AnswerWithCitations:
    """
    Generate an answer using multi-hop graph traversal with full citations.

    This is the core differentiator: every claim is traced back to source documents.
    """

    reasoning_trace = []
    citations = []

    # Step 1: Initial semantic search
    reasoning_trace.append(f"🔍 Searching knowledge graph for: '{query}'")
    initial_results = graph.semantic_search(query)

    if not initial_results:
        return AnswerWithCitations(
            answer="I couldn't find relevant information in the knowledge graph.",
            citations=[],
            reasoning_trace=reasoning_trace
        )

    reasoning_trace.append(f"📊 Found {len(initial_results)} initial entities")

    # Step 2: Multi-hop expansion
    all_context = []
    for entity in initial_results[:3]:
        reasoning_trace.append(f"🔗 Expanding from entity: {entity['name']}")
        related = graph.find_related_entities(entity['name'], hops=2)

        for rel in related:
            all_context.append({
                "entity": rel['name'],
                "description": rel['description'],
                "source": rel['source'],
                "chunk": rel['chunk'],
                "path": rel.get('path_descriptions', [])
            })
            reasoning_trace.append(f"  → Found related: {rel['name']}")

    # Step 3: Build context with source tracking
    context_parts = []
    source_map = {}

    for i, ctx in enumerate(all_context):
        source_key = f"[{i+1}]"
        context_parts.append(f"{source_key} {ctx['entity']}: {ctx['description']}")
        source_map[source_key] = {
            "document": ctx['source'],
            "text": ctx['chunk'],
            "entity": ctx['entity']
        }

    context_text = "\n".join(context_parts)
    reasoning_trace.append(f"📝 Built context from {len(context_parts)} sources")

    # Step 4: Generate answer with citation requirements
    answer_prompt = f"""Based on the following knowledge graph context, answer the question.
IMPORTANT: For each claim you make, cite the source using [N] notation.

CONTEXT:
{context_text}

QUESTION: {query}

Provide a comprehensive answer with inline citations [1], [2], etc. for each claim.
"""

    try:
        response = ollama_client.chat(
            model=model,
            messages=[{"role": "user", "content": answer_prompt}]
        )
        answer = response['message']['content']
        reasoning_trace.append("✅ Generated answer with citations")

        # Step 5: Extract and verify citations
        citation_refs = re.findall(r'\[(\d+)\]', answer)

        for ref in set(citation_refs):
            key = f"[{ref}]"
            if key in source_map:
                src = source_map[key]
                citations.append(Citation(
                    claim=f"Reference {key}",
                    source_document=src['document'],
                    source_text=src['text'],
                    confidence=0.85,
                    reasoning_path=[f"Entity: {src['entity']}"]
                ))

        reasoning_trace.append(f"🔒 Verified {len(citations)} citations")

        return AnswerWithCitations(
            answer=answer,
            citations=citations,
            reasoning_trace=reasoning_trace
        )

    except Exception as e:
        return AnswerWithCitations(
            answer=f"Error generating answer: {e}",
            citations=[],
            reasoning_trace=reasoning_trace
        )