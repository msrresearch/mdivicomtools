import logging

def setup_logging(level: int = logging.INFO):
    """
    Configure logging for the module.

    Args:
        level (int): Logging level (e.g., logging.INFO, logging.DEBUG).
    """
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=level
    )

