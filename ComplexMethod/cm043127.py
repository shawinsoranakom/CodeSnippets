def calculate_api_coverage(self, state: CrawlState, query: str) -> Dict[str, float]:
        """Calculate specialized coverage metrics for API documentation"""
        metrics = {
            'endpoint_coverage': 0.0,
            'example_coverage': 0.0,
            'parameter_coverage': 0.0
        }

        # Analyze knowledge base for API-specific content
        endpoint_patterns = [r'GET\s+/', r'POST\s+/', r'PUT\s+/', r'DELETE\s+/']
        example_patterns = [r'```\w+', r'curl\s+-', r'import\s+requests']
        param_patterns = [r'param(?:eter)?s?\s*:', r'required\s*:', r'optional\s*:']

        total_docs = len(state.knowledge_base)
        if total_docs == 0:
            return metrics

        docs_with_endpoints = 0
        docs_with_examples = 0
        docs_with_params = 0

        for doc in state.knowledge_base:
            content = doc.markdown.raw_markdown if hasattr(doc, 'markdown') else str(doc)

            # Check for endpoints
            if any(re.search(pattern, content, re.IGNORECASE) for pattern in endpoint_patterns):
                docs_with_endpoints += 1

            # Check for examples
            if any(re.search(pattern, content, re.IGNORECASE) for pattern in example_patterns):
                docs_with_examples += 1

            # Check for parameters
            if any(re.search(pattern, content, re.IGNORECASE) for pattern in param_patterns):
                docs_with_params += 1

        metrics['endpoint_coverage'] = docs_with_endpoints / total_docs
        metrics['example_coverage'] = docs_with_examples / total_docs
        metrics['parameter_coverage'] = docs_with_params / total_docs

        return metrics