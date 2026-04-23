def _build_schema_prompt(html: str, schema_type: str, query: str = None, target_json_example: str = None) -> str:
        """
        Build the prompt for schema generation. Shared by sync and async methods.

        Returns:
            str: Combined system and user prompt
        """
        from .prompts import JSON_SCHEMA_BUILDER

        prompt_template = JSON_SCHEMA_BUILDER if schema_type == "CSS" else JSON_SCHEMA_BUILDER_XPATH

        system_content = f"""You specialize in generating special JSON schemas for web scraping. This schema uses CSS or XPATH selectors to present a repetitive pattern in crawled HTML, such as a product in a product list or a search result item in a list of search results. We use this JSON schema to pass to a language model along with the HTML content to extract structured data from the HTML. The language model uses the JSON schema to extract data from the HTML and retrieve values for fields in the JSON schema, following the schema.

Generating this HTML manually is not feasible, so you need to generate the JSON schema using the HTML content. The HTML copied from the crawled website is provided below, which we believe contains the repetitive pattern.

# Schema main keys:
- name: This is the name of the schema.
- baseSelector: This is the CSS or XPATH selector that identifies the base element that contains all the repetitive patterns.
- baseFields: This is a list of fields that you extract from the base element itself.
- fields: This is a list of fields that you extract from the children of the base element. {{name, selector, type}} based on the type, you may have extra keys such as "attribute" when the type is "attribute".

# Extra Context:
In this context, the following items may or may not be present:
- Example of target JSON object: This is a sample of the final JSON object that we hope to extract from the HTML using the schema you are generating.
- Extra Instructions: This is optional instructions to consider when generating the schema provided by the user.
- Query or explanation of target/goal data item: This is a description of what data we are trying to extract from the HTML. This explanation means we're not sure about the rigid schema of the structures we want, so we leave it to you to use your expertise to create the best and most comprehensive structures aimed at maximizing data extraction from this page. You must ensure that you do not pick up nuances that may exist on a particular page. The focus should be on the data we are extracting, and it must be valid, safe, and robust based on the given HTML.

# What if there is no example of target JSON object and also no extra instructions or even no explanation of target/goal data item?
In this scenario, use your best judgment to generate the schema. You need to examine the content of the page and understand the data it provides. If the page contains repetitive data, such as lists of items, products, jobs, places, books, or movies, focus on one single item that repeats. If the page is a detailed page about one product or item, create a schema to extract the entire structured data. At this stage, you must think and decide for yourself. Try to maximize the number of fields that you can extract from the HTML.

# What are the instructions and details for this schema generation?
{prompt_template}"""

        user_content = f"""
                HTML to analyze:
                ```html
                {html}
                ```
                """

        if query:
            user_content += f"\n\n## Query or explanation of target/goal data item:\n{query}"
        if target_json_example:
            user_content += f"\n\n## Example of target JSON object:\n```json\n{target_json_example}\n```"

        if query and not target_json_example:
            user_content += """IMPORTANT: To remind you, in this process, we are not providing a rigid example of the adjacent objects we seek. We rely on your understanding of the explanation provided in the above section. Make sure to grasp what we are looking for and, based on that, create the best schema.."""
        elif not query and target_json_example:
            user_content += """IMPORTANT: Please remember that in this process, we provided a proper example of a target JSON object. Make sure to adhere to the structure and create a schema that exactly fits this example. If you find that some elements on the page do not match completely, vote for the majority."""
        elif not query and not target_json_example:
            user_content += """IMPORTANT: Since we neither have a query nor an example, it is crucial to rely solely on the HTML content provided. Leverage your expertise to determine the schema based on the repetitive patterns observed in the content."""

        user_content += """IMPORTANT:
        0/ Ensure your schema remains reliable by avoiding selectors that appear to generate dynamically and are not dependable. You want a reliable schema, as it consistently returns the same data even after many page reloads.
        1/ DO NOT USE use base64 kind of classes, they are temporary and not reliable.
        2/ Every selector must refer to only one unique element. You should ensure your selector points to a single element and is unique to the place that contains the information. You have to use available techniques based on CSS or XPATH requested schema to make sure your selector is unique and also not fragile, meaning if we reload the page now or in the future, the selector should remain reliable.
        3/ Do not use Regex as much as possible.

        Analyze the HTML and generate a JSON schema that follows the specified format. Only output valid JSON schema, nothing else.
        """

        return "\n\n".join([system_content, user_content])