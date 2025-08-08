# The #1 recommendation from OWASP for hashing is still argon2
#
# In C++, I'm stuck with OpenSSL versions too old to support it
# In Python, hashlib only has pbkdf2, and the argon2 libraries do not look good
# enough
#
# Why the fuck is the allegedly best and generally most recommended hashing
# library so fucking hard to _actually_ use?
from hashlib import pbkdf2_hmac

def hash(password: str, salt: str):
    # 2025-08: OWASP recommendation is 600000
    return pbkdf2_hmac(
        "sha512",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        1500000
    ).hex()
