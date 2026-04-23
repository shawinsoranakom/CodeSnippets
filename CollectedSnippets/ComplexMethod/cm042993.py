def generate_site(base_dir: Path, site_name: str = "FakeShop", base_path: str = ""):
    """Generates the dummy website structure."""
    base_dir.mkdir(parents=True, exist_ok=True)

    # --- Clean and prepare the base path for URL construction ---
    # Ensure it starts with '/' if not empty, and remove any trailing '/'
    if base_path:
        full_base_path = "/" + base_path.strip('/')
    else:
        full_base_path = "" # Represents the root

    print(f"Using base path for links: '{full_base_path}'")

    # --- Level 0: Homepage ---
    home_body = "<h2>Welcome to FakeShop!</h2><p>Your one-stop shop for imaginary items.</p><h3>Categories:</h3>\n<ul>"
    # Define the *actual* link path for the homepage breadcrumb
    home_link_path = f"{full_base_path}/index.html"
    breadcrumbs_home = [{"name": "Home", "link": home_link_path}] # Base breadcrumb

    # Links *within* the page content should remain relative
    for i in range(NUM_CATEGORIES):
        cat_name = f"Category-{i+1}"
        cat_folder_name = quote(cat_name.lower().replace(" ", "-"))
        # This path is relative to the current directory (index.html)
        cat_relative_page_path = f"{cat_folder_name}/index.html"
        home_body += f'<li><a class="category-link" href="{cat_relative_page_path}">{cat_name}</a> - {generate_lorem(10)}</li>'
    home_body += "</ul>"
    create_html_page(base_dir / "index.html", "Homepage", home_body, []) # No breadcrumbs *on* the homepage itself

    # --- Levels 1-5 ---
    for i in range(NUM_CATEGORIES):
        cat_name = f"Category-{i+1}"
        cat_folder_name = quote(cat_name.lower().replace(" ", "-"))
        cat_dir = base_dir / cat_folder_name
        # This is the *absolute* path for the breadcrumb link
        cat_link_path = f"{full_base_path}/{cat_folder_name}/index.html"
        # Update breadcrumbs list for this level
        breadcrumbs_cat = breadcrumbs_home + [{"name": cat_name, "link": cat_link_path}]

        # --- Level 1: Category Page ---
        cat_body = f"<p>{generate_lorem(15)} for {cat_name}.</p><h3>Sub-Categories:</h3>\n<ul>"
        for j in range(NUM_SUBCATEGORIES_PER_CAT):
            subcat_name = f"{cat_name}-Sub-{j+1}"
            subcat_folder_name = quote(subcat_name.lower().replace(" ", "-"))
            # Path relative to the category page
            subcat_relative_page_path = f"{subcat_folder_name}/index.html"
            cat_body += f'<li><a class="subcategory-link" href="{subcat_relative_page_path}">{subcat_name}</a> - {generate_lorem(8)}</li>'
        cat_body += "</ul>"
        # Pass the updated breadcrumbs list
        create_html_page(cat_dir / "index.html", cat_name, cat_body, breadcrumbs_home) # Parent breadcrumb needed here

        for j in range(NUM_SUBCATEGORIES_PER_CAT):
            subcat_name = f"{cat_name}-Sub-{j+1}"
            subcat_folder_name = quote(subcat_name.lower().replace(" ", "-"))
            subcat_dir = cat_dir / subcat_folder_name
            # Absolute path for the breadcrumb link
            subcat_link_path = f"{full_base_path}/{cat_folder_name}/{subcat_folder_name}/index.html"
            # Update breadcrumbs list for this level
            breadcrumbs_subcat = breadcrumbs_cat + [{"name": subcat_name, "link": subcat_link_path}]

            # --- Level 2: Sub-Category Page (Product List) ---
            subcat_body = f"<p>Explore products in {subcat_name}. {generate_lorem(12)}</p><h3>Products:</h3>\n<ul class='product-list'>"
            for k in range(NUM_PRODUCTS_PER_SUBCAT):
                prod_id = f"P{i+1}{j+1}{k+1:03d}" # e.g., P11001
                prod_name = f"{subcat_name} Product {k+1} ({prod_id})"
                # Filename relative to the subcategory page
                prod_filename = f"product_{prod_id}.html"
                # Absolute path for the breadcrumb link
                prod_link_path = f"{full_base_path}/{cat_folder_name}/{subcat_folder_name}/{prod_filename}"

                # Preview on list page (link remains relative)
                subcat_body += f"""
                <li>
                    <div class="product-preview">
                        <a class="product-link" href="{prod_filename}"><strong>{prod_name}</strong></a>
                        <p>{generate_lorem(10)}</p>
                        <span class="product-price">£{random.uniform(10, 500):.2f}</span>
                    </div>
                </li>"""

                # --- Level 3: Product Page ---
                prod_price = random.uniform(10, 500)
                prod_desc = generate_lorem(40)
                prod_specs = {f"Spec {s+1}": generate_lorem(3) for s in range(random.randint(3,6))}
                prod_reviews_count = random.randint(0, 150)
                # Relative filenames for links on this page
                details_filename_relative = f"product_{prod_id}_details.html"
                reviews_filename_relative = f"product_{prod_id}_reviews.html"

                prod_body = f"""
                <p class="product-price">Price: £{prod_price:.2f}</p>
                <div class="product-description">
                    <h2>Description</h2>
                    <p>{prod_desc}</p>
                </div>
                <div class="product-specs">
                    <h2>Specifications</h2>
                    <ul>
                        {''.join(f'<li><span class="spec-name">{name}</span>: <span class="spec-value">{value}</span></li>' for name, value in prod_specs.items())}
                    </ul>
                </div>
                <div class="product-reviews">
                    <h2>Reviews</h2>
                    <p>Total Reviews: <span class="review-count">{prod_reviews_count}</span></p>
                </div>
                <hr>
                <p>
                    <a class="details-link" href="{details_filename_relative}">View More Details</a> |
                    <a class="reviews-link" href="{reviews_filename_relative}">See All Reviews</a>
                </p>
                """
                # Update breadcrumbs list for this level
                breadcrumbs_prod = breadcrumbs_subcat + [{"name": prod_name, "link": prod_link_path}]
                # Pass the updated breadcrumbs list
                create_html_page(subcat_dir / prod_filename, prod_name, prod_body, breadcrumbs_subcat) # Parent breadcrumb needed here

                # --- Level 4: Product Details Page ---
                details_filename = f"product_{prod_id}_details.html" # Actual filename
                # Absolute path for the breadcrumb link
                details_link_path = f"{full_base_path}/{cat_folder_name}/{subcat_folder_name}/{details_filename}"
                details_body = f"<p>This page contains extremely detailed information about {prod_name}.</p>{generate_lorem(100)}"
                # Update breadcrumbs list for this level
                breadcrumbs_details = breadcrumbs_prod + [{"name": "Details", "link": details_link_path}]
                # Pass the updated breadcrumbs list
                create_html_page(subcat_dir / details_filename, f"{prod_name} - Details", details_body, breadcrumbs_prod) # Parent breadcrumb needed here

                # --- Level 5: Product Reviews Page ---
                reviews_filename = f"product_{prod_id}_reviews.html" # Actual filename
                # Absolute path for the breadcrumb link
                reviews_link_path = f"{full_base_path}/{cat_folder_name}/{subcat_folder_name}/{reviews_filename}"
                reviews_body = f"<p>All {prod_reviews_count} reviews for {prod_name} are listed here.</p><ul>"
                for r in range(prod_reviews_count):
                     reviews_body += f"<li>Review {r+1}: {generate_lorem(random.randint(15, 50))}</li>"
                reviews_body += "</ul>"
                # Update breadcrumbs list for this level
                breadcrumbs_reviews = breadcrumbs_prod + [{"name": "Reviews", "link": reviews_link_path}]
                # Pass the updated breadcrumbs list
                create_html_page(subcat_dir / reviews_filename, f"{prod_name} - Reviews", reviews_body, breadcrumbs_prod) # Parent breadcrumb needed here


            subcat_body += "</ul>" # Close product-list ul
            # Pass the correct breadcrumbs list for the subcategory index page
            create_html_page(subcat_dir / "index.html", subcat_name, subcat_body, breadcrumbs_cat)