# Email Configuration for Password Reset

To enable email sending for password reset functionality, you need to configure SMTP settings.

## For Render Deployment

1. Go to your Render dashboard
2. Select your web service
3. Go to "Environment" tab
4. Add the following environment variables:

### Required Variables:
- `SMTP_SERVER` - Your SMTP server (e.g., `smtp.gmail.com`, `smtp.sendgrid.net`)
- `SMTP_PORT` - SMTP port (usually `587` for TLS or `465` for SSL)
- `SMTP_USER` - Your SMTP username/email
- `SMTP_PASSWORD` - Your SMTP password or app password
- `FROM_EMAIL` (optional) - Email address to send from (defaults to SMTP_USER)

### Example: Gmail Setup

1. Enable 2-factor authentication on your Gmail account
2. Generate an "App Password":
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a password for "Mail"
3. Set these environment variables in Render:
   ```
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   FROM_EMAIL=your-email@gmail.com
   ```

### Example: SendGrid Setup

1. Create a SendGrid account
2. Create an API key with "Mail Send" permissions
3. Set these environment variables in Render:
   ```
   SMTP_SERVER=smtp.sendgrid.net
   SMTP_PORT=587
   SMTP_USER=apikey
   SMTP_PASSWORD=your-sendgrid-api-key
   FROM_EMAIL=noreply@yourdomain.com
   ```

### Example: Mailgun Setup

1. Create a Mailgun account
2. Get your SMTP credentials from the dashboard
3. Set these environment variables in Render:
   ```
   SMTP_SERVER=smtp.mailgun.org
   SMTP_PORT=587
   SMTP_USER=your-mailgun-username
   SMTP_PASSWORD=your-mailgun-password
   FROM_EMAIL=noreply@yourdomain.com
   ```

## For Local Development

Create a `.env` file in the project root (this file is gitignored):

```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
```

Or set them as environment variables:

```bash
export SMTP_SERVER=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USER=your-email@gmail.com
export SMTP_PASSWORD=your-app-password
export FROM_EMAIL=your-email@gmail.com
```

## Testing

1. If email is NOT configured, the reset code will be shown in the response (for development)
2. If email IS configured, the code will be sent via email and NOT shown in the response
3. Check your email inbox (and spam folder) for the reset code

## Troubleshooting

- **Emails not sending**: Check that all SMTP environment variables are set correctly
- **Authentication errors**: Verify your SMTP credentials are correct
- **Port issues**: Try port 465 with SSL instead of 587 with TLS
- **Gmail issues**: Make sure you're using an App Password, not your regular password
- **Check logs**: Look at Render logs for email sending errors

