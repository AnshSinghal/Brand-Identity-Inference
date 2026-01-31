import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def get_api_key() -> Optional[str]:
    return os.environ.get("GROQ_API_KEY")
