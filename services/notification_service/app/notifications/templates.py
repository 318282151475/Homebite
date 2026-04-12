# Email templates for each event
# In production you would use Jinja2 templates or a service like SendGrid
# Keeping simple HTML strings here for clarity


def welcome_email(full_name: str) -> dict:
    return {
        "subject": "Welcome to HomeBite!",
        "body": f"""
            <h2>Welcome to HomeBite, {full_name}!</h2>
            <p>We connect you with the best home chefs in your city.</p>
            <p>Start exploring homemade meals near you.</p>
            <br/>
            <p>Team HomeBite</p>
        """
    }


def order_placed_email(order_id: int, total_amount: float) -> dict:
    return {
        "subject": f"Order #{order_id} Confirmed!",
        "body": f"""
            <h2>Your order has been placed!</h2>
            <p>Order ID: <strong>#{order_id}</strong></p>
            <p>Total Amount: <strong>₹{total_amount}</strong></p>
            <p>We are finding the best available chef for you. 
               You will be notified once a chef is assigned.</p>
            <br/>
            <p>Team HomeBite</p>
        """
    }


def chef_assigned_email(order_id: int, chef_name: str) -> dict:
    return {
        "subject": f"Chef Assigned for Order #{order_id}",
        "body": f"""
            <h2>Your chef is confirmed!</h2>
            <p>Order ID: <strong>#{order_id}</strong></p>
            <p>Chef: <strong>{chef_name}</strong> is preparing your meal.</p>
            <p>Estimated delivery time: 45 minutes.</p>
            <br/>
            <p>Team HomeBite</p>
        """
    }


def delivery_started_email(order_id: int) -> dict:
    return {
        "subject": f"Order #{order_id} is Out for Delivery!",
        "body": f"""
            <h2>Your order is on the way!</h2>
            <p>Order ID: <strong>#{order_id}</strong></p>
            <p>Your food has been picked up and is heading your way.</p>
            <p>Please be available at your delivery address.</p>
            <br/>
            <p>Team HomeBite</p>
        """
    }


def delivery_completed_email(order_id: int) -> dict:
    return {
        "subject": f"Order #{order_id} Delivered!",
        "body": f"""
            <h2>Your order has been delivered!</h2>
            <p>Order ID: <strong>#{order_id}</strong></p>
            <p>We hope you enjoy your meal.</p>
            <p>Please rate your experience on the app.</p>
            <br/>
            <p>Team HomeBite</p>
        """
    }


def chef_assignment_failed_email(order_id: int) -> dict:
    return {
        "subject": f"Order #{order_id} — No Chef Available",
        "body": f"""
            <h2>We're sorry!</h2>
            <p>Order ID: <strong>#{order_id}</strong></p>
            <p>Unfortunately no chef is available in your area right now.</p>
            <p>Your order has been cancelled. A full refund will be processed.</p>
            <br/>
            <p>Team HomeBite</p>
        """
    }