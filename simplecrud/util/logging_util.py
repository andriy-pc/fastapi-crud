import datetime
import json
import logging
import sys


class LoggingJsonFormatter(logging.Formatter):
    def __init__(self) -> None:
        super().__init__()
        empty_log_record = logging.LogRecord("", 0, "", 0, None, None, None)
        self.reserved_keys = set(empty_log_record.__dict__.keys())
        # Do not log "color_message" - used by uvicorn
        self.reserved_keys.add("color_message")

    def format(self, record: logging.LogRecord) -> str:
        # Use 'getMessage' here, see https://stackoverflow.com/a/46399669
        record.message = record.getMessage()
        message_dict = {
            "timestamp": f"{datetime.datetime.utcnow().isoformat()[:-3]}Z",
            "level": record.levelname,
            "thread": record.threadName,
            "name": record.name,
            "file": record.filename,
            "lineno": record.lineno,
            "func": record.funcName,
        }
        if record.message:
            message_dict["message"] = record.message
        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            message_dict["exc_info"] = record.exc_text
        if record.stack_info:
            message_dict["stack_info"] = self.formatStack(record.stack_info)
        # Add the  dict items specified by the "extra" logging argument (if any)
        for k, v in record.__dict__.items():
            if k not in self.reserved_keys and k not in message_dict:
                message_dict[k] = v
        return json.dumps(message_dict)


_logging_handler = logging.StreamHandler()


def setup_json_formatted_logging() -> None:
    global _logging_handler

    handler = logging.StreamHandler(sys.stdout)
    logging_json_formatter = LoggingJsonFormatter()
    handler.setFormatter(logging_json_formatter)
    handler.setLevel(logging.NOTSET)
    _logging_handler = handler

    # Remove and replace any pre-existing log handler
    logger = logging.getLogger()
    previous_handlers = logger.handlers
    logger.handlers = []
    for previous_handler in previous_handlers:
        previous_handler.close()
    logger.addHandler(handler)


def disable_logging_json_formatting() -> None:
    _logging_handler.setFormatter(logging.Formatter())
