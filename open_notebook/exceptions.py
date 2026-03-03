class OpenNotebookError(Exception):
    """Base exception class for Synapse errors."""

    pass


class DatabaseOperationError(OpenNotebookError):
    """Raised when a database operation fails."""

    pass


class UnsupportedTypeException(OpenNotebookError):
    """Raised when an unsupported type is provided."""

    pass


class InvalidInputError(OpenNotebookError):
    """Raised when invalid input is provided."""

    pass


class NotFoundError(OpenNotebookError):
    """Raised when a requested resource is not found."""

    pass


class AuthenticationError(OpenNotebookError):
    """Raised when there's an authentication problem."""

    pass


class ConfigurationError(OpenNotebookError):
    """Raised when there's a configuration problem."""

    pass


class SchemaValidationError(OpenNotebookError):
    """Raised when an LLM response fails structural validation persistently."""
    def __init__(self, message: str, errors: list, retries_used: int, raw_output_excerpt: str):
        super().__init__(message)
        self.error_code = "SCHEMA_VALIDATION_FAILED"
        self.errors = errors
        self.retries_used = retries_used
        self.raw_output_excerpt = raw_output_excerpt

    def to_dict(self):
        return {
            "error": self.error_code,
            "message": str(self),
            "retries": self.retries_used,
            "details": self.errors,
            "raw_excerpt": self.raw_output_excerpt
        }


class ExternalServiceError(OpenNotebookError):
    """Raised when an external service (e.g., AI model) fails."""

    pass


class RateLimitError(OpenNotebookError):
    """Raised when a rate limit is exceeded."""

    pass


class FileOperationError(OpenNotebookError):
    """Raised when a file operation fails."""

    pass


class NetworkError(OpenNotebookError):
    """Raised when a network operation fails."""

    pass


class NoTranscriptFound(OpenNotebookError):
    """Raised when no transcript is found for a video."""

    pass
