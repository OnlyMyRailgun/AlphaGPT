import asyncio
from loguru import logger
from .data_manager import DataManager
from .config import Config

async def main():
    try:
        Config.validate_runtime()
    except ValueError as exc:
        logger.error(str(exc))
        return

    logger.info(f"Starting pipeline with DATA_PROVIDER={Config.DATA_PROVIDER}")

    manager = DataManager()
    
    try:
        await manager.initialize()
        await manager.pipeline_sync_daily()
    except Exception as e:
        logger.exception(f"Pipeline crashed: {e}")
    finally:
        await manager.close()

if __name__ == "__main__":
    asyncio.run(main())
