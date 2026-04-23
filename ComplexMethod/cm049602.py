def configurator_apply(self, **kwargs):
        website = self.get_current_website()
        theme_name = kwargs['theme_name']
        theme = self.env['ir.module.module'].search([('name', '=', theme_name)])
        redirect_url = theme.button_choose_theme()

        website.configurator_done = True

        # Enable tour
        tour_asset_id = self.env.ref('website.configurator_tour')
        tour_asset_id.copy({'key': tour_asset_id.key, 'website_id': website.id, 'active': True})

        # Set logo from generated attachment or from company's logo
        logo_attachment_id = kwargs.get('logo_attachment_id')
        company = website.company_id
        if logo_attachment_id:
            attachment = self.env['ir.attachment'].browse(logo_attachment_id)
            attachment.write({
                'res_model': 'website',
                'res_field': 'logo',
                'res_id': website.id,
            })
        elif not logo_attachment_id and not company.uses_default_logo:
            website.logo = company.logo.decode('utf-8')

        # Configure the color palette
        selected_palette = kwargs.get('selected_palette')
        if selected_palette:
            Assets = self.env['website.assets']
            selected_palette_name = selected_palette if isinstance(selected_palette, str) else 'base-1'
            Assets.make_scss_customization(
                '/website/static/src/scss/options/user_values.scss',
                {'color-palettes-name': "'%s'" % selected_palette_name}
            )
            if isinstance(selected_palette, list):
                Assets.make_scss_customization(
                    '/website/static/src/scss/options/colors/user_color_palette.scss',
                    {f'o-color-{i}': color for i, color in enumerate(selected_palette, 1)}
                )

        # Update CTA
        cta_data = website.get_cta_data(kwargs.get('website_purpose'), kwargs.get('website_type'))
        if cta_data['cta_btn_text']:
            xpath_view = 'website.snippets'
            parent_view = self.env['website'].with_context(website_id=website.id).viewref(xpath_view)
            self.env['ir.ui.view'].create({
                'name': parent_view.key + ' CTA',
                'key': parent_view.key + "_cta",
                'inherit_id': parent_view.id,
                'website_id': website.id,
                'type': 'qweb',
                'priority': 32,
                'arch_db': """
                    <data>
                        <xpath expr="//t[@t-set='cta_btn_href']" position="replace">
                            <t t-set="cta_btn_href">%s</t>
                        </xpath>
                        <xpath expr="//t[@t-set='cta_btn_text']" position="replace">
                            <t t-set="cta_btn_text">%s</t>
                        </xpath>
                    </data>
                """ % (cta_data['cta_btn_href'], cta_data['cta_btn_text'])
            })
            try:
                view_id = self.env['website'].viewref('website.header_call_to_action')
                if view_id:
                    el = etree.fromstring(view_id.arch_db)
                    btn_cta_el = el.xpath("//a[hasclass('btn_cta')]")
                    if btn_cta_el:
                        btn_cta_el[0].attrib['href'] = cta_data['cta_btn_href']
                        btn_cta_el[0].text = cta_data['cta_btn_text']
                    view_id.with_context(website_id=website.id).write({'arch_db': etree.tostring(el)})
            except ValueError as e:
                logger.warning(e)

        # Configure the features
        features = self.env['website.configurator.feature'].browse(kwargs.get('selected_features'))

        menu_company = self.env['website.menu']
        if len(features.filtered('menu_sequence')) > 5 and len(features.filtered('menu_company')) > 1:
            menu_company = self.env['website.menu'].create({
                'name': _('Company'),
                'parent_id': website.menu_id.id,
                'website_id': website.id,
                'sequence': 40,
            })

        pages_views = {}
        modules = self.env['ir.module.module']
        module_data = {}
        for feature in features:
            add_menu = bool(feature.menu_sequence)
            if feature.module_id:
                if feature.module_id.state != 'installed':
                    modules += feature.module_id
                if add_menu:
                    if feature.module_id.name != 'website_blog':
                        module_data[feature.feature_url] = {'sequence': feature.menu_sequence}
                    else:
                        blogs = module_data.setdefault('#blog', [])
                        blogs.append({'name': feature.name, 'sequence': feature.menu_sequence})
            elif feature.page_view_id:
                result = self.env['website'].new_page(
                    name=feature.name,
                    add_menu=add_menu,
                    page_values=dict(url=feature.feature_url, is_published=True),
                    menu_values=add_menu and {
                        'url': feature.feature_url,
                        'sequence': feature.menu_sequence,
                        'parent_id': feature.menu_company and menu_company.id or website.menu_id.id,
                    },
                    template=feature.page_view_id.key
                )
                pages_views[feature.iap_page_code] = result['view_id']

        if modules:
            modules.button_immediate_install()

        self.env['website'].browse(website.id).configurator_set_menu_links(menu_company, module_data)

        # Extension hook: allows installed modules (e.g. website_sale, website_blog, ...) to perform
        # additional setup steps on the generated website. This acts as an entry point for modules to
        # customize the website.
        self.env['website'].configurator_addons_apply(**kwargs)

        # We need to refresh the environment of the website because we installed
        # some new module and we need the overrides of these new menus e.g. for
        # the call to `get_cta_data`.
        website = self.env['website'].browse(website.id)

        # Update footers links, needs to be done after "Features" addition to go
        # through module overrides of `configurator_get_footer_links`.
        footer_links = website.configurator_get_footer_links()
        footer_ids = [
            'website.template_footer_contact',
            'website.footer_custom', 'website.template_footer_links',
            'website.template_footer_minimalist', 'website.template_footer_mega', 'website.template_footer_mega_columns', 'website.template_footer_mega_links',
        ]
        for footer_id in footer_ids:
            view_id = self.env['website'].viewref(footer_id)
            if view_id:
                # Deliberately hardcode dynamic code inside the view arch,
                # it will be transformed into static nodes after a save/edit
                # thanks to the t-ignore in parents node.
                try:
                    arch_string = etree.fromstring(view_id.arch_db)
                except etree.XMLSyntaxError as e:
                    # The xml view could have been modified in the backend, we don't
                    # want the xpath error to break the configurator feature
                    logger.warning("Failed to update footer links in view %s: %s", footer_id, e)
                else:
                    el = arch_string.xpath("//t[@t-set='configurator_footer_links']")
                    if not el:
                        logger.warning("No 'configurator_footer_links' found in view %s", footer_id)
                        continue
                    el[0].attrib['t-value'] = json.dumps(footer_links)
                    view_id.with_context(website_id=website.id).write({'arch_db': etree.tostring(arch_string)})

        # Load suggestion from iap for selected pages
        industry_id = kwargs['industry_id']
        custom_resources = self._website_api_rpc(
            '/api/website/2/configurator/custom_resources/%s' % (industry_id if industry_id > 0 else ''),
            {'theme': theme_name}
        )

        # Generate text for the pages
        requested_pages = set(pages_views.keys()).union({'homepage'})
        configurator_snippets = website.get_theme_configurator_snippets(theme_name)
        industry = kwargs['industry_name']

        IrQweb = self.env['ir.qweb'].with_context(website_id=website.id, lang=website.default_lang_id.code)
        text_generation_target_lang = self.get_current_website().default_lang_id.code
        # If the target language is not English, we need a good translation
        # coverage. But if the target lang is en_XX it's ok to have en_US text.
        text_must_be_translated_for_openai = not text_generation_target_lang.startswith('en_')

        # Initialize HTML processor with context chaining - similar to website.with_context() pattern
        html_text_processor = self.env['website.html.text.processor']._with_processing_context(
            IrQweb=IrQweb,
            cta_data=cta_data,
            text_generation_target_lang=text_generation_target_lang,
            text_must_be_translated_for_openai=text_must_be_translated_for_openai,
        )
        generated_content = {}
        translated_content = {}
        for page_code in requested_pages - {'privacy_policy'}:
            snippet_list = configurator_snippets.get(page_code, [])
            for snippet in snippet_list:
                snippet_key = website._get_snippet_view_key(snippet, page_code)
                html_text_processor, snippet_generated_content, snippet_translated_content = html_text_processor._get_snippet_content(snippet_key)
                generated_content.update(snippet_generated_content)
                translated_content.update(snippet_translated_content)

        translated_ratio = html_text_processor._calculate_translation_ratio(generated_content, translated_content)
        if translated_ratio > 0.8:
            try:
                database_id = self.env['ir.config_parameter'].sudo().get_param('database.uuid')
                response = self._OLG_api_rpc('/api/olg/1/generate_placeholder', {
                    'placeholders': list(generated_content.keys()),
                    'lang': website.default_lang_id.name,
                    'industry': industry,
                    'database_id': database_id,
                })
                name_replace_parser = re.compile(r"XXXX", re.MULTILINE)
                website_name = re.escape(website.name)
                for key in generated_content:
                    if response.get(key):
                        generated_content[key] = (name_replace_parser.sub(website_name, response[key], 0))
            except AccessError:
                # If IAP is broken continue normally (without generating text)
                pass
        else:
            logger.info("Skip AI text generation because translation coverage is too low (%s%%)", translated_ratio * 100)

        # Configure the pages
        for index, page_code in enumerate(requested_pages):
            snippet_list = configurator_snippets.get(page_code, [])
            if page_code == 'homepage':
                page_view_id = self.with_context(website_id=website.id).viewref('website.homepage')
            else:
                page_view_id = self.env['ir.ui.view'].browse(pages_views[page_code])
            rendered_snippets = []
            nb_snippets = len(snippet_list)
            for i, snippet in enumerate(snippet_list, start=1):
                try:
                    snippet_key = website._get_snippet_view_key(snippet, page_code)
                    el = html_text_processor._update_snippet_content(generated_content, snippet_key)

                    # Add the data-snippet attribute to identify the snippet
                    # for compatibility code
                    el.attrib['data-snippet'] = snippet

                    # Theme specific customizations for non-website snippets
                    theme_customizations = get_manifest(theme_name).get('theme_customizations', {})
                    customizations = theme_customizations.get(snippet, {})

                    # Configure non-website snippet with defaults and theme-level customizations.
                    website._preconfigure_snippet(snippet, el, customizations)

                    # Remove the previews needed for the snippets dialog
                    dialog_preview_els = el.find_class('s_dialog_preview')
                    for preview_el in dialog_preview_els:
                        preview_el.getparent().remove(preview_el)

                    # Tweak the shape of the first snippet to connect it
                    # properly with the header color in some themes
                    if i == 1:
                        shape_el = el.xpath("//*[hasclass('o_we_shape')]")
                        if shape_el:
                            shape_el[0].attrib['class'] += ' o_header_extra_shape_mapping'

                    # Tweak the shape of the last snippet to connect it
                    # properly with the footer color in some themes
                    if i == nb_snippets:
                        shape_el = el.xpath("//*[hasclass('o_we_shape')]")
                        if shape_el:
                            shape_el[0].attrib['class'] += ' o_footer_extra_shape_mapping'
                    rendered_snippet = etree.tostring(el, encoding='unicode')
                    rendered_snippets.append(rendered_snippet)
                except ValueError as e:
                    logger.warning(e)
            page_view_id.save(value=f'<div class="oe_structure">{"".join(rendered_snippets)}</div>',
                              xpath="(//div[hasclass('oe_structure')])[last()]")
            # Copy the configurator pages to preserve the original untouched
            # pages in the landing page category when creating a new page.
            page_view_id.copy({
                'key': f"{index}_{page_view_id.key}_configurator_pages_landing",
                'website_id': website.id,
            })

        # Configure the images
        images = custom_resources.get('images', {})
        names = self.env['ir.model.data'].search([
            ('name', '=ilike', f'configurator\\_{website.id}\\_%'),
            ('module', '=', 'website'),
            ('model', '=', 'ir.attachment')
        ]).mapped('name')
        for name, image_src in images.items():
            extn_identifier = 'configurator_%s_%s' % (website.id, name.split('.')[1])
            if extn_identifier in names:
                continue
            try:
                response = requests.get(image_src, timeout=3)
                response.raise_for_status()
            except Exception as e:
                logger.warning("Failed to download image: %s.\n%s", image_src, e)
            else:
                attachment = self.env['ir.attachment'].create({
                    'name': name,
                    'website_id': website.id,
                    'key': name,
                    'type': 'binary',
                    'raw': response.content,
                    'public': True,
                })
                self.env['ir.model.data'].create({
                    'name': extn_identifier,
                    'module': 'website',
                    'model': 'ir.attachment',
                    'res_id': attachment.id,
                    'noupdate': True,
                })

        def fallback_create_missing_industry_image(image_name, fallback_img_name):
            """ If an industry did not specify an image, this method allows that
            specific image to be using the same image as another fallback one.
            """
            image_name = f'website.{image_name}'
            if (
                image_name not in images.keys()
                and f'website.{fallback_img_name}' in images.keys()
            ):
                extn_identifier = 'configurator_%s_%s' % (website.id, image_name.split('.')[1])
                if extn_identifier not in names:
                    attachment = self.env['ir.attachment'].create({
                        'name': image_name,
                        'website_id': website.id,
                        'key': image_name,
                        'type': 'binary',
                        'raw': self.env.ref(f'website.configurator_{website.id}_{fallback_img_name}').raw,
                        'public': True,
                    })
                    self.env['ir.model.data'].create({
                        'name': extn_identifier,
                        'module': 'website',
                        'model': 'ir.attachment',
                        'res_id': attachment.id,
                        'noupdate': True,
                    })

        try:
            # TODO: Remove this try/except, safety net because it was merged
            #       to close to OXP.
            fallback_create_missing_industry_image('s_intro_pill_default_image', 'library_image_10')
            fallback_create_missing_industry_image('s_intro_pill_default_image_2', 'library_image_14')
            fallback_create_missing_industry_image('s_banner_default_image_2', 's_image_text_default_image')
            fallback_create_missing_industry_image('s_banner_default_image_3', 's_product_list_default_image_1')
            fallback_create_missing_industry_image('s_striped_top_default_image', 's_picture_default_image')
            fallback_create_missing_industry_image('s_text_cover_default_image', 's_cover_default_image')
            fallback_create_missing_industry_image('s_showcase_default_image', 's_image_text_default_image')
            fallback_create_missing_industry_image('s_image_hexagonal_default_image', 's_cover_default_image')
            fallback_create_missing_industry_image('s_image_hexagonal_default_image_1', 's_company_team_image_1')
            fallback_create_missing_industry_image('s_accordion_image_default_image', 's_image_text_default_image')
            fallback_create_missing_industry_image('s_pricelist_boxed_default_background', 's_product_catalog_default_image')
            fallback_create_missing_industry_image('s_image_title_default_image', 's_cover_default_image')
            fallback_create_missing_industry_image('s_key_images_default_image_1', 's_media_list_default_image_1')
            fallback_create_missing_industry_image('s_key_images_default_image_2', 's_image_text_default_image')
            fallback_create_missing_industry_image('s_key_images_default_image_3', 's_media_list_default_image_2')
            fallback_create_missing_industry_image('s_key_images_default_image_4', 's_text_image_default_image')
            fallback_create_missing_industry_image('s_kickoff_default_image', 's_cover_default_image')
            fallback_create_missing_industry_image('s_quadrant_default_image_1', 'library_image_03')
            fallback_create_missing_industry_image('s_quadrant_default_image_2', 'library_image_10')
            fallback_create_missing_industry_image('s_quadrant_default_image_3', 'library_image_13')
            fallback_create_missing_industry_image('s_quadrant_default_image_4', 'library_image_05')
            fallback_create_missing_industry_image('s_sidegrid_default_image_1', 'library_image_03')
            fallback_create_missing_industry_image('s_sidegrid_default_image_2', 'library_image_10')
            fallback_create_missing_industry_image('s_sidegrid_default_image_3', 'library_image_13')
            fallback_create_missing_industry_image('s_sidegrid_default_image_4', 'library_image_05')
            fallback_create_missing_industry_image('s_cta_box_default_image', 'library_image_02')
            fallback_create_missing_industry_image('s_image_punchy_default_image', 's_cover_default_image')
            fallback_create_missing_industry_image('s_image_frame_default_image', 's_carousel_default_image_2')
            fallback_create_missing_industry_image('s_carousel_intro_default_image_1', 's_cover_default_image')
            fallback_create_missing_industry_image('s_carousel_intro_default_image_2', 's_image_text_default_image')
            fallback_create_missing_industry_image('s_carousel_intro_default_image_3', 's_text_image_default_image')
            fallback_create_missing_industry_image('s_website_form_overlay_default_image', 's_cover_default_image')
            fallback_create_missing_industry_image('s_website_form_cover_default_image', 's_cover_default_image')
            fallback_create_missing_industry_image('s_split_intro_default_image', 's_cover_default_image')
            fallback_create_missing_industry_image('s_framed_intro_default_image', 's_cover_default_image')
            fallback_create_missing_industry_image('s_wavy_grid_default_image_1', 's_cover_default_image')
            fallback_create_missing_industry_image('s_wavy_grid_default_image_2', 's_image_text_default_image')
            fallback_create_missing_industry_image('s_wavy_grid_default_image_3', 's_text_image_default_image')
            fallback_create_missing_industry_image('s_wavy_grid_default_image_4', 's_carousel_default_image_1')
            fallback_create_missing_industry_image('s_timeline_images_default_image_1', 's_media_list_default_image_1')
            fallback_create_missing_industry_image('s_timeline_images_default_image_2', 's_media_list_default_image_2')
            fallback_create_missing_industry_image('s_carousel_cards_default_image_1', 's_carousel_default_image_1')
            fallback_create_missing_industry_image('s_carousel_cards_default_image_2', 's_carousel_default_image_2')
            fallback_create_missing_industry_image('s_carousel_cards_default_image_3', 's_carousel_default_image_3')
            fallback_create_missing_industry_image('s_banner_connected_default_image', 's_cover_default_image')

        except Exception:
            pass

        return {'url': redirect_url, 'website_id': website.id}