import jwt
import time

from totoms.model.TotoConfig import TotoControllerConfig


def new_toto_service_token(config: TotoControllerConfig) -> str:
    """Generate a JWT service token for service-to-service authentication.

    The token represents a service (not a user). The user field is set to "toto-service".

    Args:
        config: TotoControllerConfig containing the JWT signing key.

    Returns:
        A signed JWT token string.
    """
    exp = int(time.time()) + 3 * 60 * 60  # 3 hours from now

    token = jwt.encode(
        {"user": "toto-service", "authProvider": "toto", "exp": exp},
        config.jwt_key,
        algorithm="HS256",
    )

    return token
