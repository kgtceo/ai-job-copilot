"""ai-job-copilot — a grounded, evaluated LLM pipeline for job applications."""

from .client import CopilotClient, StructuredCallError
from .config import Settings
from .models import CopilotReport
from .pipeline import Copilot

__all__ = [
    "Copilot",
    "CopilotClient",
    "CopilotReport",
    "Settings",
    "StructuredCallError",
]
__version__ = "0.1.0"
