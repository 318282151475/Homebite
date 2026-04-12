from fastapi import HTTPException, status


class OrderNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )


class InvalidOrderStatusTransitionException(HTTPException):
    def __init__(self, current: str, requested: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition order from '{current}' to '{requested}'",
        )


class OrderCancellationNotAllowedException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order can only be cancelled when in PENDING or CHEF_ASSIGNED status",
        )