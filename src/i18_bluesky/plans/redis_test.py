import asyncio
from typing import Set

import bluesky.plan_stubs as bps
from blueskt.devices import TetrammDetector
from bluesky.protocols import Readable
from dodal.common import MsgGenerator
from dodal.plans.data_session_metadata import attach_data_session_metadata_decorator

from i18_bluesky.redis_client import RedisClient

DEFAULT_DETECTORS = set()
DEFAULT_BASELINE_MEASUREMENTS = set()


async def fetch_from_redis(key: str) -> str:
    redis = await RedisClient.get_instance()
    value = await redis.get(key)
    return value.decode() if value else None


@attach_data_session_metadata_decorator()
def check_detectors(
    num_frames: int = 1,
    devices: Set[Readable] = DEFAULT_DETECTORS | DEFAULT_BASELINE_MEASUREMENTS,
) -> MsgGenerator:
    """
    Take a reading from all devices that are used in the
    stopflow plan by default.
    """

    # Ensure the Redis client is initialized at the start of the plan
    asyncio.run(RedisClient.get_instance())

    # Example use: fetch a value from Redis
    redis_key = "some_key"
    redis_value = asyncio.run(fetch_from_redis(redis_key))
    print(f"Fetched from Redis: {redis_value}")

    # Tetramms do not support software triggering
    software_triggerable_devices = {
        device for device in devices if not isinstance(device, TetrammDetector)
    }
    yield from bps.count(
        software_triggerable_devices,
        num=num_frames,
    )
