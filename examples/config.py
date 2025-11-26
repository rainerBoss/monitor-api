import logging
import sys

def logging_config() -> None:
    root = logging.getLogger("")
    root.setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel("INFO")
    logging.getLogger("httpcore").setLevel("INFO")

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - [ %(levelname)s ] - %(name)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)