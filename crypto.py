"""
crypto.py  –  AES-CBC decrypt helpers
Same logic as appex_v5.py  (key = 638udh3829162018, iv = fedcba9876543210)
"""

import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from config import AES_KEY, AES_IV


def aes_decrypt(enc: str) -> str:
    """
    Decrypt a ClassX-encrypted string.
    Format:  base64(ciphertext):base64(iv_override)   — we only use the first part.
    """
    if not enc:
        return ""
    try:
        raw = base64.b64decode(enc.split(":")[0])
        if len(raw) == 0:
            return ""
        cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
        return unpad(cipher.decrypt(raw), AES.block_size).decode("utf-8")
    except Exception as e:
        return f"[decrypt_error: {e}]"


def decode_b64(encoded: str) -> str:
    try:
        return base64.b64decode(encoded).decode("utf-8")
    except Exception as e:
        return f"[b64_error: {e}]"


def decrypt_video_data(data: dict) -> dict:
    """
    Given a video-details data dict, decrypt all encrypted fields in-place
    and add *_decrypted keys.
    """
    # download_link
    dl = data.get("download_link", "")
    if dl:
        data["download_link_decrypted"] = aes_decrypt(dl)

    # encrypted_links list
    for link in data.get("encrypted_links", []):
        if link.get("path"):
            link["path_decrypted"] = aes_decrypt(link["path"])
        if link.get("key"):
            k1 = aes_decrypt(link["key"])
            link["key_decrypted"] = decode_b64(k1) if k1 and "error" not in k1 else k1

    # pdf links inside VIDEO material
    if data.get("material_type") == "VIDEO":
        for field_pair in [("pdf_link", "pdf_encryption_key"), ("pdf_link2", "pdf2_encryption_key")]:
            plink, pkey = field_pair
            p = data.get(plink, "")
            k = data.get(pkey, "")
            if p:
                data[f"{plink}_decrypted"] = aes_decrypt(p)
            if k:
                dk = aes_decrypt(k)
                data[f"{pkey}_decrypted"] = dk if dk != "abcdefg" else ""

    return data
