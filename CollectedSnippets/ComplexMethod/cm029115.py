async def extract_clean_markdown(
	browser_session: 'BrowserSession | None' = None,
	dom_service: DomService | None = None,
	target_id: str | None = None,
	extract_links: bool = False,
	extract_images: bool = False,
) -> tuple[str, dict[str, Any]]:
	"""Extract clean markdown from browser content using enhanced DOM tree.

	This unified function can extract markdown using either a browser session (for tools service)
	or a DOM service with target ID (for page actor).

	Args:
	    browser_session: Browser session to extract content from (tools service path)
	    dom_service: DOM service instance (page actor path)
	    target_id: Target ID for the page (required when using dom_service)
	    extract_links: Whether to preserve links in markdown
	    extract_images: Whether to preserve inline image src URLs in markdown

	Returns:
	    tuple: (clean_markdown_content, content_statistics)

	Raises:
	    ValueError: If neither browser_session nor (dom_service + target_id) are provided
	"""
	# Validate input parameters
	if browser_session is not None:
		if dom_service is not None or target_id is not None:
			raise ValueError('Cannot specify both browser_session and dom_service/target_id')
		# Browser session path (tools service)
		enhanced_dom_tree = await _get_enhanced_dom_tree_from_browser_session(browser_session)
		current_url = await browser_session.get_current_page_url()
		method = 'enhanced_dom_tree'
	elif dom_service is not None and target_id is not None:
		# DOM service path (page actor)
		# Lazy fetch all_frames inside get_dom_tree if needed (for cross-origin iframes)
		enhanced_dom_tree, _ = await dom_service.get_dom_tree(target_id=target_id, all_frames=None)
		current_url = None  # Not available via DOM service
		method = 'dom_service'
	else:
		raise ValueError('Must provide either browser_session or both dom_service and target_id')

	# Use the HTML serializer with the enhanced DOM tree
	html_serializer = HTMLSerializer(extract_links=extract_links)
	page_html = html_serializer.serialize(enhanced_dom_tree)

	original_html_length = len(page_html)

	# Use markdownify for clean markdown conversion
	from markdownify import markdownify as md

	# 'td', 'th', and headings are the only elements where markdownify sets the _inline context,
	# which causes img elements to be stripped to just alt text when keep_inline_images_in=[]
	_keep_inline_images_in = ['td', 'th', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'] if extract_images else []
	content = md(
		page_html,
		heading_style='ATX',  # Use # style headings
		strip=['script', 'style'],  # Remove these tags
		bullets='-',  # Use - for unordered lists
		code_language='',  # Don't add language to code blocks
		escape_asterisks=False,  # Don't escape asterisks (cleaner output)
		escape_underscores=False,  # Don't escape underscores (cleaner output)
		escape_misc=False,  # Don't escape other characters (cleaner output)
		autolinks=False,  # Don't convert URLs to <> format
		default_title=False,  # Don't add default title attributes
		keep_inline_images_in=_keep_inline_images_in,  # Include image src URLs when extract_images=True
	)

	initial_markdown_length = len(content)

	# Minimal cleanup - markdownify already does most of the work
	content = re.sub(r'%[0-9A-Fa-f]{2}', '', content)  # Remove any remaining URL encoding

	# Apply light preprocessing to clean up excessive whitespace
	content, chars_filtered = _preprocess_markdown_content(content)

	final_filtered_length = len(content)

	# Content statistics
	stats = {
		'method': method,
		'original_html_chars': original_html_length,
		'initial_markdown_chars': initial_markdown_length,
		'filtered_chars_removed': chars_filtered,
		'final_filtered_chars': final_filtered_length,
	}

	# Add URL to stats if available
	if current_url:
		stats['url'] = current_url

	return content, stats