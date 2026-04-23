def main():
    set_sidebar()

    # Check if API keys are set
    if not all([st.session_state.qdrant_host, 
                st.session_state.qdrant_api_key, 
                st.session_state.gemini_api_key]):
        st.warning("Please configure your API keys in the sidebar first")
        return

    # Initialize components
    embedding_model, client, db = initialize_components()
    if not all([embedding_model, client, db]):
        return

    # Initialize retriever and tools
    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 5})
    retriever_tool = create_retriever_tool(
        retriever,
        "retrieve_blog_posts",
        "Search and return information about blog posts on LLMs, LLM agents, prompt engineering, and adversarial attacks on LLMs.",
    )
    tools = [retriever_tool]

    # URL input section
    url = st.text_input(
        ":link: Paste the blog link:",
        placeholder="e.g., https://lilianweng.github.io/posts/2023-06-23-agent/"
    )
    if st.button("Enter URL"):
        if url:
            with st.spinner("Processing documents..."):
                if add_documents_to_qdrant(url, db):
                    st.success("Documents added successfully!")
                else:
                    st.error("Failed to add documents")
        else:
            st.warning("Please enter a URL")

    # Query section
    graph = get_graph(retriever_tool)
    query = st.text_area(
        ":bulb: Enter your query about the blog post:",
        placeholder="e.g., What does Lilian Weng say about the types of agent memory?"
    )

    if st.button("Submit Query"):
        if not query:
            st.warning("Please enter a query")
            return

        inputs = {"messages": [HumanMessage(content=query)]}
        with st.spinner("Generating response..."):
            try:
                response = generate_message(graph, inputs)
                st.write(response)
            except Exception as e:
                st.error(f"Error generating response: {str(e)}")

    st.markdown("---")
    st.write("Built with :blue-background[LangChain] | :blue-background[LangGraph] by [Charan](https://www.linkedin.com/in/codewithcharan/)")