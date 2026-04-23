def browser_process(self) -> None:
        def _is_local_runtime() -> bool:
            runtime_flag = os.getenv('RUNTIME', '').lower()
            return runtime_flag == 'local'

        # Default Playwright cache for local runs only; do not override in docker
        if _is_local_runtime() and 'PLAYWRIGHT_BROWSERS_PATH' not in os.environ:
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(
                Path.home() / '.cache' / 'playwright'
            )

        if self.eval_mode:
            assert self.browsergym_eval_env is not None
            logger.info('Initializing browser env for web browsing evaluation.')
            if not self.browsergym_eval_env.startswith('browsergym/'):
                self.browsergym_eval_env = 'browsergym/' + self.browsergym_eval_env
            if 'visualwebarena' in self.browsergym_eval_env:
                import browsergym.visualwebarena  # noqa F401 register visualwebarena tasks as gym environments
                import nltk

                nltk.download('punkt_tab')
            elif 'webarena' in self.browsergym_eval_env:
                import browsergym.webarena  # noqa F401 register webarena tasks as gym environments
            elif 'miniwob' in self.browsergym_eval_env:
                import browsergym.miniwob  # noqa F401 register miniwob tasks as gym environments
            else:
                raise ValueError(
                    f'Unsupported browsergym eval env: {self.browsergym_eval_env}'
                )
            env = gym.make(self.browsergym_eval_env, tags_to_mark='all', timeout=100000)
        else:
            downloads_path = os.getenv('BROWSERGYM_DOWNLOAD_DIR')
            if not downloads_path and _is_local_runtime():
                downloads_path = str(Path.home() / '.cache' / 'browsergym-downloads')
            if not downloads_path:
                downloads_path = '/workspace/.downloads/'
            env = gym.make(
                'browsergym/openended',
                task_kwargs={'start_url': 'about:blank', 'goal': 'PLACEHOLDER_GOAL'},
                wait_for_user_message=False,
                headless=True,
                disable_env_checker=True,
                tags_to_mark='all',
                timeout=100000,
                pw_context_kwargs={'accept_downloads': True},
                pw_chromium_kwargs={'downloads_path': downloads_path},
            )
        obs, info = env.reset()

        logger.info('Successfully called env.reset')
        # EVAL ONLY: save the goal into file for evaluation
        self.eval_goal = None
        self.goal_image_urls = []
        self.eval_rewards: list[float] = []
        if self.eval_mode:
            self.eval_goal = obs['goal']
            if 'goal_object' in obs:
                obs['goal_object'] = list(obs['goal_object'])
                if len(obs['goal_object']) > 0:
                    self.eval_goal = obs['goal_object'][0]['text']
                for message in obs['goal_object']:
                    if message['type'] == 'image_url':
                        image_src = message['image_url']
                        if isinstance(image_src, dict):
                            image_src = image_src['url']
                        self.goal_image_urls.append(image_src)
            logger.debug(f'Browsing goal: {self.eval_goal}')
        logger.info('Browser env started.')

        while should_continue():
            try:
                if self.browser_side.poll(timeout=0.01):
                    unique_request_id, action_data = self.browser_side.recv()

                    # shutdown the browser environment
                    if unique_request_id == 'SHUTDOWN':
                        logger.debug('SHUTDOWN recv, shutting down browser env...')
                        env.close()
                        return
                    elif unique_request_id == 'IS_ALIVE':
                        self.browser_side.send(('ALIVE', None))
                        continue

                    # EVAL ONLY: Get evaluation info
                    if action_data['action'] == BROWSER_EVAL_GET_GOAL_ACTION:
                        self.browser_side.send(
                            (
                                unique_request_id,
                                {
                                    'text_content': self.eval_goal,
                                    'image_content': self.goal_image_urls,
                                },
                            )
                        )
                        continue
                    elif action_data['action'] == BROWSER_EVAL_GET_REWARDS_ACTION:
                        self.browser_side.send(
                            (
                                unique_request_id,
                                {'text_content': json.dumps(self.eval_rewards)},
                            )
                        )
                        continue

                    action = action_data['action']
                    obs, reward, terminated, truncated, info = env.step(action)

                    # EVAL ONLY: Save the rewards into file for evaluation
                    if self.eval_mode:
                        self.eval_rewards.append(reward)

                    # add text content of the page
                    html_str = flatten_dom_to_str(obs['dom_object'])
                    obs['text_content'] = self.html_text_converter.handle(html_str)
                    # make observation serializable
                    obs['set_of_marks'] = image_to_png_base64_url(
                        overlay_som(
                            obs['screenshot'], obs.get('extra_element_properties', {})
                        ),
                        add_data_prefix=True,
                    )
                    obs['screenshot'] = image_to_png_base64_url(
                        obs['screenshot'], add_data_prefix=True
                    )
                    obs['active_page_index'] = obs['active_page_index'].item()
                    obs['elapsed_time'] = obs['elapsed_time'].item()
                    self.browser_side.send((unique_request_id, obs))
            except KeyboardInterrupt:
                logger.debug('Browser env process interrupted by user.')
                try:
                    env.close()
                except Exception:
                    pass
                return