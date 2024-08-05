from typing import Optional

import aioredis


class RedisClient:
    _instance: Optional[aioredis.Redis] = None

    @classmethod
    async def get_instance(cls) -> aioredis.Redis:
        if cls._instance is None:
            cls._instance = await aioredis.create_redis_pool("redis-service:6379")
        return cls._instance

    @classmethod
    async def close_instance(cls):
        if cls._instance is not None:
            cls._instance.close()
            await cls._instance.wait_closed()
            cls._instance = None


# Usage in your plan function
async def fetch_from_redis(key: str) -> str:
    redis = await RedisClient.get_instance()
    value = await redis.get(key)
    return value.decode() if value else None


# Remember to close the instance when the application shuts down
async def shutdown():
    await RedisClient.close_instance()
