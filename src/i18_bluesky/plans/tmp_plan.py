
from dodal.plans.data_session_metadata import attach_data_session_metadata_decorator
import asyncio
from typing import Set
from aioredis import Redis
from bluesky import plan_stubs as bps
from bluesky import MsgGenerator

class Readable:
    pass

class TetrammDetector(Readable):
    pass

DEFAULT_DETECTORS = set()
DEFAULT_BASELINE_MEASUREMENTS = set()

async def fetch_from_redis(key: str) -> str:
    """Asynchronous function to fetch data from Redis."""
    redis = Redis()
    try:
        value = await redis.get(key)
        return value.decode() if value else None
    finally:
        await redis.close()

@attach_data_session_metadata_decorator()
def check_detectors_for_stopflow(
    num_frames: int = 1,
    devices: Set[Readable] = DEFAULT_DETECTORS | DEFAULT_BASELINE_MEASUREMENTS,
) -> MsgGenerator:
    """
    Take a reading from all devices that are used in the
    stopflow plan by default.
    """

    # Asynchronously fetch some value from Redis
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
