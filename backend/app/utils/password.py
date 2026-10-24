import bcrypt


def hash_password(password: str) -> str:
    """对用户密码加密"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """验证加密密码"""
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
