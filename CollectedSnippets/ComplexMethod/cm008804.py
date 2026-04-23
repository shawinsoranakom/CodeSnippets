def decrypt_fragment(fragment, frag_content):
            if frag_content is None:
                return
            decrypt_info = fragment.get('decrypt_info')
            if not decrypt_info or decrypt_info['METHOD'] != 'AES-128':
                return frag_content
            iv = decrypt_info.get('IV') or struct.pack('>8xq', fragment['media_sequence'])
            decrypt_info['KEY'] = (decrypt_info.get('KEY')
                                   or _get_key(traverse_obj(info_dict, ('hls_aes', 'uri')) or decrypt_info['URI']))
            # Don't decrypt the content in tests since the data is explicitly truncated and it's not to a valid block
            # size (see https://github.com/ytdl-org/youtube-dl/pull/27660). Tests only care that the correct data downloaded,
            # not what it decrypts to.
            if self.params.get('test', False):
                return frag_content
            return unpad_pkcs7(aes_cbc_decrypt_bytes(frag_content, decrypt_info['KEY'], iv))