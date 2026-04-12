from fastapi import HTTPException, status


class LogNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log entry not found",
        )