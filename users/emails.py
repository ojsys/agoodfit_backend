from datetime import datetime
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_welcome_email(user):
    """Send a welcome email to a newly registered user.

    Fails silently so it never blocks registration.
    """
    try:
        context = {
            'username': user.username,
            'email': user.email,
            'year': datetime.now().year,
        }

        subject = 'Welcome to A Good Fit! 🎉'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = user.email

        text_body = render_to_string('emails/welcome.txt', context)
        html_body = render_to_string('emails/welcome.html', context)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_email,
            to=[to_email],
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send()

        logger.info('Welcome email sent to %s', to_email)
    except Exception as exc:
        logger.error('Failed to send welcome email to %s: %s', user.email, exc)


def send_password_reset_email(user, token):
    """Send a password-reset link. Fails silently."""
    try:
        reset_url = f"{getattr(settings, 'FRONTEND_URL', 'https://agoodfit.app')}/reset-password?token={token}&uid={user.pk}"
        context = {
            'username': user.username,
            'reset_url': reset_url,
            'year': datetime.now().year,
        }
        subject = 'Reset your A Good Fit password'
        text_body = (
            f"Hi {user.username},\n\n"
            f"Click the link below to reset your password:\n{reset_url}\n\n"
            f"If you didn't request this, you can ignore this email.\n\n"
            f"— The A Good Fit Team"
        )
        html_body = (
            f"<p>Hi <strong>{user.username}</strong>,</p>"
            f"<p>Click the button below to reset your password:</p>"
            f'<p><a href="{reset_url}" style="background:#6C63FF;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;display:inline-block;">Reset Password</a></p>'
            f"<p>If you didn't request this, you can ignore this email.</p>"
            f"<p>— The A Good Fit Team</p>"
        )
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send()
        logger.info('Password reset email sent to %s', user.email)
    except Exception as exc:
        logger.error('Failed to send password reset email to %s: %s', user.email, exc)
