def _output_build_progress(
        self, current_line: dict, layers: dict, previous_layer_count: int
    ) -> None:
        if 'id' in current_line and 'progressDetail' in current_line:
            layer_id = current_line['id']
            if layer_id not in layers:
                layers[layer_id] = {'status': '', 'progress': '', 'last_logged': 0}

            if 'status' in current_line:
                layers[layer_id]['status'] = current_line['status']

            if 'progress' in current_line:
                layers[layer_id]['progress'] = current_line['progress']

            if 'progressDetail' in current_line:
                progress_detail = current_line['progressDetail']
                if 'total' in progress_detail and 'current' in progress_detail:
                    total = progress_detail['total']
                    current = progress_detail['current']
                    percentage = min(
                        (current / total) * 100, 100
                    )  # Ensure it doesn't exceed 100%
                else:
                    percentage = (
                        100 if layers[layer_id]['status'] == 'Download complete' else 0
                    )

            if self.rolling_logger.is_enabled():
                self.rolling_logger.move_back(previous_layer_count)
                for lid, layer_data in sorted(layers.items()):
                    self.rolling_logger.replace_current_line()
                    status = layer_data['status']
                    progress = layer_data['progress']
                    if status == 'Download complete':
                        self.rolling_logger.write_immediately(
                            f'Layer {lid}: Download complete'
                        )
                    elif status == 'Already exists':
                        self.rolling_logger.write_immediately(
                            f'Layer {lid}: Already exists'
                        )
                    else:
                        self.rolling_logger.write_immediately(
                            f'Layer {lid}: {progress} {status}'
                        )
            elif percentage != 0 and (
                percentage - layers[layer_id]['last_logged'] >= 10 or percentage == 100
            ):
                logger.debug(
                    f'Layer {layer_id}: {layers[layer_id]["progress"]} {layers[layer_id]["status"]}'
                )

            layers[layer_id]['last_logged'] = percentage
        elif 'status' in current_line:
            logger.debug(current_line['status'])