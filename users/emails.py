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
