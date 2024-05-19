#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from base64 import b64encode, b64decode

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class AESCipher:
    def __init__(self, key='A3s68aORSgHs$71P', iv=b'\x00' * 16):
        self.key = key.encode('utf-8')
        self.iv = iv

    def encrypt(self, data):
        self.cipher = AES.new(self.key, AES.MODE_CBC, iv=self.iv)
        byte_string = b64encode(self.cipher.encrypt(pad(data.encode('utf-8'),
                                                        AES.block_size)))
        return byte_string.decode('utf-8')

    def decrypt(self, data):
        raw = b64decode(data)
        self.cipher = AES.new(self.key, AES.MODE_CBC, iv=self.iv)
        return unpad(self.cipher.decrypt(raw), AES.block_size).decode('utf-8')


if __name__ == '__main__':

    msg = '{"userid":"username@domain.com","password":"password"}'

    print('TESTING ENCRYPTION')
    aes = AESCipher()
    encrypted = aes.encrypt(msg)
    print('Ciphertext:\n', encrypted)

    print('\nTESTING DECRYPTION')
    print('Message...:', aes.decrypt(encrypted))
