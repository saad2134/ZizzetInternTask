import contextvars
import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict

correlation_id_ctx = contextvars.ContextVar[str]("correlation_id", default="")
tenant_id_ctx = contextvars.ContextVar[str]("tenant_id", default="")


class StructuredJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_ctx.get(),
            "tenant_id": tenant_id_ctx.get(),
        }

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_obj.update(record.extra)

        return json.dumps(log_obj)


def setup_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJsonFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]

    # Silence verbose 3rd party logs
    logging.getLogger("uvicorn.access").handlers = [handler]
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


logger = logging.getLogger("zizzet.recovery")
