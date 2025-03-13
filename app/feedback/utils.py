"""
Helper functions for feedback app.
"""

import qrcode
from django.conf import settings
from io import BytesIO
import base64


def generate_qr_code(invite_id):
    """Generate a QR code linking to the invitation URL"""
    invite_url = "InviteURL"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(invite_url)
    qr.make(fit=True)

    img = qr.make_image(fill="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")

    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{qr_code_base64}"