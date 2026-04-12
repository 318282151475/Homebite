from fastapi import HTTPException, status


class DeliveryNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found",
        )


class DeliveryAlreadyExistsException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Delivery record already exists for this order",
        )


class InvalidDeliveryStatusTransitionException(HTTPException):
    def __init__(self, current: str, requested: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition delivery from '{current}' to '{requested}'",
        )