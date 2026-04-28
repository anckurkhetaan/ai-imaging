import logging
import sys
from config import Config
from pipeline import Pipeline


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("pipeline.log", encoding="utf-8"),
        ],
    )


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        config = Config()
        logger.info("Config loaded successfully.")
    except KeyError as e:
        logger.error(f"Missing required environment variable: {e}")
        sys.exit(1)

    pipeline = Pipeline(config)
    pipeline.run()


if __name__ == "__main__":
    main()