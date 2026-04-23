def main():
    st.set_page_config(
        page_title="Knowledge Graph RAG with Citations",
        page_icon="🔍",
        layout="wide"
    )

    st.title("🔍 Knowledge Graph RAG with Verifiable Citations")
    st.markdown("""
    This demo shows how **Knowledge Graph-based RAG** provides:
    - **Multi-hop reasoning** across connected information
    - **Verifiable source attribution** for every claim
    - **Transparent reasoning traces** you can audit

    Unlike traditional vector RAG, every answer is traceable to its source documents.
    """)

    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")

    neo4j_uri = st.sidebar.text_input("Neo4j URI", "bolt://localhost:7687")
    neo4j_user = st.sidebar.text_input("Neo4j User", "neo4j")
    neo4j_password = st.sidebar.text_input("Neo4j Password", type="password", value="password")
    llm_model = st.sidebar.selectbox("LLM Model", ["llama3.2", "mistral", "phi3"])

    # Initialize session state
    if 'graph_initialized' not in st.session_state:
        st.session_state.graph_initialized = False
        st.session_state.documents = []

    # Main content
    tab1, tab2, tab3 = st.tabs(["📄 Add Documents", "❓ Ask Questions", "🔬 View Graph"])

    with tab1:
        st.header("Step 1: Build Knowledge Graph from Documents")

        sample_docs = {
            "AI Research Paper": """
            GraphRAG is a technique developed by Microsoft Research that combines knowledge graphs 
            with retrieval-augmented generation. Unlike traditional RAG which uses vector similarity,
            GraphRAG builds a structured knowledge graph from documents, enabling multi-hop reasoning.
            The technique was introduced by researchers including Darren Edge and Ha Trinh.
            GraphRAG excels at answering complex questions that require connecting information 
            from multiple sources, such as "What are the relationships between different research projects?"
            """,
            "Company Report": """
            Acme Corp was founded in 2020 by Jane Smith and John Doe in San Francisco.
            The company develops AI-powered analytics tools for enterprise customers.
            Their flagship product, DataSense, uses machine learning to analyze business data.
            Jane Smith previously worked at Google as a senior engineer on the TensorFlow team.
            John Doe was a co-founder of StartupX, which was acquired by Microsoft in 2019.
            Acme Corp raised $50 million in Series B funding led by Sequoia Capital.
            """
        }

        doc_choice = st.selectbox("Choose sample document:", list(sample_docs.keys()))
        doc_text = st.text_area("Or paste your own document:", sample_docs[doc_choice], height=200)
        doc_name = st.text_input("Document name:", doc_choice)

        if st.button("🔨 Extract & Add to Knowledge Graph"):
            with st.spinner("Extracting entities and relationships..."):
                try:
                    graph = KnowledgeGraphManager(neo4j_uri, neo4j_user, neo4j_password)
                    entities, relationships = extract_entities_with_llm(doc_text, doc_name, llm_model)

                    for entity in entities:
                        graph.add_entity(entity)

                    for rel in relationships:
                        graph.add_relationship(rel)

                    graph.close()

                    st.success(f"✅ Extracted {len(entities)} entities and {len(relationships)} relationships")

                    with st.expander("View Extracted Entities"):
                        for e in entities:
                            st.write(f"**{e.name}** ({e.entity_type}): {e.description}")

                    with st.expander("View Extracted Relationships"):
                        for r in relationships:
                            st.write(f"{r.source} --[{r.relation_type}]--> {r.target}: {r.description}")

                    st.session_state.graph_initialized = True
                    st.session_state.documents.append(doc_name)

                except Exception as e:
                    st.error(f"Error: {e}")
                    st.info("Make sure Neo4j is running and Ollama has the model pulled.")

    with tab2:
        st.header("Step 2: Ask Questions with Verifiable Answers")

        if not st.session_state.graph_initialized:
            st.warning("⚠️ Please add documents to the knowledge graph first.")
        else:
            st.info(f"📚 Knowledge graph contains documents: {', '.join(st.session_state.documents)}")

        query = st.text_input("Enter your question:", "What are the key concepts in GraphRAG and who developed it?")

        if st.button("🔍 Ask with Citations"):
            with st.spinner("Traversing knowledge graph and generating answer..."):
                try:
                    graph = KnowledgeGraphManager(neo4j_uri, neo4j_user, neo4j_password)
                    result = generate_answer_with_citations(query, graph, llm_model)
                    graph.close()

                    # Display reasoning trace
                    st.subheader("🧠 Reasoning Trace")
                    for step in result.reasoning_trace:
                        st.write(step)

                    # Display answer
                    st.subheader("💬 Answer")
                    st.markdown(result.answer)

                    # Display citations
                    st.subheader("📚 Source Citations")
                    if result.citations:
                        for i, citation in enumerate(result.citations):
                            with st.expander(f"Citation {i+1}: {citation.source_document}"):
                                st.write(f"**Source Document:** {citation.source_document}")
                                st.write(f"**Source Text:** {citation.source_text}")
                                st.write(f"**Confidence:** {citation.confidence:.0%}")
                                st.write(f"**Reasoning Path:** {' → '.join(citation.reasoning_path)}")
                    else:
                        st.info("No specific citations extracted for this answer.")

                except Exception as e:
                    st.error(f"Error: {e}")

    with tab3:
        st.header("🔬 Knowledge Graph Visualization")
        st.info("This tab shows the structure of your knowledge graph.")

        if st.button("📊 Show Graph Statistics"):
            try:
                graph = KnowledgeGraphManager(neo4j_uri, neo4j_user, neo4j_password)
                with graph.driver.session() as session:
                    node_count = session.run("MATCH (n) RETURN count(n) as count").single()['count']
                    rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()['count']

                col1, col2 = st.columns(2)
                col1.metric("Total Entities", node_count)
                col2.metric("Total Relationships", rel_count)

                graph.close()
            except Exception as e:
                st.error(f"Error connecting to Neo4j: {e}")

        if st.button("🗑️ Clear Graph"):
            try:
                graph = KnowledgeGraphManager(neo4j_uri, neo4j_user, neo4j_password)
                graph.clear_graph()
                graph.close()
                st.session_state.graph_initialized = False
                st.session_state.documents = []
                st.success("Graph cleared!")
            except Exception as e:
                st.error(f"Error: {e}")