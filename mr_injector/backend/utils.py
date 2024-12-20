import hashlib


def hash_text(text):
    # Convert the text to bytes
    text_bytes = text.encode('utf-8')

    # Create a SHA-256 hash object
    hash_object = hashlib.sha256()

    # Update the hash object with the bytes
    hash_object.update(text_bytes)

    # Get the hexadecimal representation of the hash
    hash_hex = hash_object.hexdigest()

    return hash_hex