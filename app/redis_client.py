import redis
from app.config import REDIS_URL
import logging
from typing import Optional


logger = logging.getLogger(__name__)

redis_pool = redis.ConnectionPool.from_url(REDIS_URL, decode_responses=True)




class RedisSession:
    """Lightweight context manager for using redis. Redis client backed by a shared pool"""

    def __init__(self, *, socket_connect_timeout: Optional[float] = 5.0):
        self.client = redis.Redis(connection_pool=redis_pool, socket_connect_timeout=socket_connect_timeout)

    def __enter__(self) -> redis.Redis:
        try:
            self.client.ping()
        except redis.RedisError:
            logger.exception("Redis ping failed in RedisSession.__enter__")
            raise
        return self.client
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False