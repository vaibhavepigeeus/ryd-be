from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from decouple import config
import base64
import hashlib
import os

salt = os.urandom(16)
passphrase = config("ENCRYPTION_KEY", default="ryd-dev-encryption-key").encode("utf-8")


def derive_key(passphrase_bytes, salt_bytes):
    return hashlib.pbkdf2_hmac("sha512", passphrase_bytes, salt_bytes, 10000, dklen=32)


key = derive_key(passphrase, salt)


def encrypt_text(plaintext):
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(plaintext.encode()) + padder.finalize()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    return base64.b64encode(salt + iv + ciphertext).decode("utf-8")


def decrypt_text(b64_ciphertext):
    try:
        ciphertext = base64.b64decode(b64_ciphertext)
        salt_bytes = ciphertext[:16]
        iv = ciphertext[16:32]
        actual_ciphertext = ciphertext[32:]
        derived_key = derive_key(passphrase, salt_bytes)
        cipher = Cipher(algorithms.AES(derived_key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        padded_plaintext = decryptor.update(actual_ciphertext) + decryptor.finalize()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        return plaintext.decode()
    except Exception:
        return b64_ciphertext


def is_decrypted(text):
    try:
        decoded = base64.b64decode(text)
        if len(decoded) < 48:
            return True
    except Exception:
        return True
    try:
        decrypt_text(text)
        return False
    except Exception:
        return True
