def __call__(self, img_list, tqdm_enable=False, tqdm_desc="OCR-rec Predict"):
        img_num = len(img_list)
        # Calculate the aspect ratio of all text bars
        width_list = []
        for img in img_list:
            width_list.append(img.shape[1] / float(img.shape[0]))
        # Sorting can speed up the recognition process
        indices = np.argsort(np.array(width_list))

        # rec_res = []
        rec_res = [['', 0.0]] * img_num
        batch_num = self.rec_batch_num
        elapse = 0
        # for beg_img_no in range(0, img_num, batch_num):
        with tqdm(total=img_num, desc=tqdm_desc, disable=not tqdm_enable) as pbar:
            index = 0
            for beg_img_no in range(0, img_num, batch_num):
                end_img_no = min(img_num, beg_img_no + batch_num)
                norm_img_batch = []
                max_wh_ratio = width_list[indices[end_img_no - 1]]
                for ino in range(beg_img_no, end_img_no):
                    if self.rec_algorithm == "SAR":
                        norm_img, _, _, valid_ratio = self.resize_norm_img_sar(
                            img_list[indices[ino]], self.rec_image_shape)
                        norm_img = norm_img[np.newaxis, :]
                        valid_ratio = np.expand_dims(valid_ratio, axis=0)
                        valid_ratios = []
                        valid_ratios.append(valid_ratio)
                        norm_img_batch.append(norm_img)

                    elif self.rec_algorithm == "SVTR":
                        norm_img = self.resize_norm_img_svtr(img_list[indices[ino]],
                                                             self.rec_image_shape)
                        norm_img = norm_img[np.newaxis, :]
                        norm_img_batch.append(norm_img)
                    elif self.rec_algorithm == "SRN":
                        norm_img = self.process_image_srn(img_list[indices[ino]],
                                                          self.rec_image_shape, 8,
                                                          self.max_text_length)
                        encoder_word_pos_list = []
                        gsrm_word_pos_list = []
                        gsrm_slf_attn_bias1_list = []
                        gsrm_slf_attn_bias2_list = []
                        encoder_word_pos_list.append(norm_img[1])
                        gsrm_word_pos_list.append(norm_img[2])
                        gsrm_slf_attn_bias1_list.append(norm_img[3])
                        gsrm_slf_attn_bias2_list.append(norm_img[4])
                        norm_img_batch.append(norm_img[0])
                    elif self.rec_algorithm == "CAN":
                        norm_img = self.norm_img_can(img_list[indices[ino]],
                                                     max_wh_ratio)
                        norm_img = norm_img[np.newaxis, :]
                        norm_img_batch.append(norm_img)
                        norm_image_mask = np.ones(norm_img.shape, dtype='float32')
                        word_label = np.ones([1, 36], dtype='int64')
                        norm_img_mask_batch = []
                        word_label_list = []
                        norm_img_mask_batch.append(norm_image_mask)
                        word_label_list.append(word_label)
                    else:
                        norm_img = self.resize_norm_img(img_list[indices[ino]],
                                                        max_wh_ratio)
                        norm_img = norm_img[np.newaxis, :]
                        norm_img_batch.append(norm_img)
                norm_img_batch = np.concatenate(norm_img_batch)
                norm_img_batch = norm_img_batch.copy()

                if self.rec_algorithm == "SRN":
                    starttime = time.time()
                    encoder_word_pos_list = np.concatenate(encoder_word_pos_list)
                    gsrm_word_pos_list = np.concatenate(gsrm_word_pos_list)
                    gsrm_slf_attn_bias1_list = np.concatenate(
                        gsrm_slf_attn_bias1_list)
                    gsrm_slf_attn_bias2_list = np.concatenate(
                        gsrm_slf_attn_bias2_list)

                    with torch.no_grad():
                        inp = torch.from_numpy(norm_img_batch)
                        encoder_word_pos_inp = torch.from_numpy(encoder_word_pos_list)
                        gsrm_word_pos_inp = torch.from_numpy(gsrm_word_pos_list)
                        gsrm_slf_attn_bias1_inp = torch.from_numpy(gsrm_slf_attn_bias1_list)
                        gsrm_slf_attn_bias2_inp = torch.from_numpy(gsrm_slf_attn_bias2_list)

                        inp = inp.to(self.device)
                        encoder_word_pos_inp = encoder_word_pos_inp.to(self.device)
                        gsrm_word_pos_inp = gsrm_word_pos_inp.to(self.device)
                        gsrm_slf_attn_bias1_inp = gsrm_slf_attn_bias1_inp.to(self.device)
                        gsrm_slf_attn_bias2_inp = gsrm_slf_attn_bias2_inp.to(self.device)

                        backbone_out = self.net.backbone(inp) # backbone_feat
                        prob_out = self.net.head(backbone_out, [encoder_word_pos_inp, gsrm_word_pos_inp, gsrm_slf_attn_bias1_inp, gsrm_slf_attn_bias2_inp])
                    # preds = {"predict": prob_out[2]}
                    preds = {"predict": prob_out["predict"]}

                elif self.rec_algorithm == "SAR":
                    starttime = time.time()
                    # valid_ratios = np.concatenate(valid_ratios)
                    # inputs = [
                    #     norm_img_batch,
                    #     valid_ratios,
                    # ]

                    with torch.no_grad():
                        inp = torch.from_numpy(norm_img_batch)
                        inp = inp.to(self.device)
                        preds = self.net(inp)

                elif self.rec_algorithm == "CAN":
                    starttime = time.time()
                    norm_img_mask_batch = np.concatenate(norm_img_mask_batch)
                    word_label_list = np.concatenate(word_label_list)
                    inputs = [norm_img_batch, norm_img_mask_batch, word_label_list]

                    inp = [torch.from_numpy(e_i) for e_i in inputs]
                    inp = [e_i.to(self.device) for e_i in inp]
                    with torch.no_grad():
                        outputs = self.net(inp)
                        outputs = [v.cpu().numpy() for k, v in enumerate(outputs)]

                    preds = outputs

                else:
                    starttime = time.time()

                    with torch.no_grad():
                        inp = torch.from_numpy(norm_img_batch)
                        inp = inp.to(self.device)
                        preds = self.net(inp)

                with torch.no_grad():
                    rec_result = self.postprocess_op(preds)

                for rno in range(len(rec_result)):
                    rec_res[indices[beg_img_no + rno]] = rec_result[rno]
                elapse += time.time() - starttime

                # 更新进度条，每次增加batch_size，但要注意最后一个batch可能不足batch_size
                current_batch_size = min(batch_num, img_num - index * batch_num)
                index += 1
                pbar.update(current_batch_size)

        # Fix NaN values in recognition results
        for i in range(len(rec_res)):
            text, score = rec_res[i]
            if isinstance(score, float) and math.isnan(score):
                rec_res[i] = (text, 0.0)

        return rec_res, elapse