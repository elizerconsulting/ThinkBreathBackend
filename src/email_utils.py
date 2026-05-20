import os

import resend
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY", "")
_FROM_EMAIL    = os.getenv("FROM_EMAIL", "onboarding@resend.dev")
_FRONTEND_URL  = os.getenv("FRONTEND_URL", "http://localhost:5173")


def _reset_email_html(to_name: str, reset_url: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Reset your ThinkBreath password</title>
</head>
<body style="margin:0;padding:0;background:#f4f4f5;font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" role="presentation"
         style="background:#f4f4f5;padding:48px 20px;">
    <tr>
      <td align="center">
        <table width="520" cellpadding="0" cellspacing="0" role="presentation"
               style="background:#ffffff;border-radius:16px;overflow:hidden;
                      box-shadow:0 2px 20px rgba(0,0,0,0.08);max-width:520px;width:100%;">

          <!-- Header gradient -->
          <tr>
            <td style="background:linear-gradient(135deg,#f472b6 0%,#7c3aed 100%);
                       padding:36px 40px 32px;">
              <p style="margin:0;font-size:19px;font-weight:700;color:#ffffff;
                        letter-spacing:-0.3px;">ThinkBreath</p>
              <p style="margin:6px 0 0;font-size:13px;color:rgba(255,255,255,0.72);">
                Mindfulness, redefined
              </p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:40px 40px 32px;">
              <h1 style="margin:0 0 10px;font-size:26px;font-weight:800;
                         color:#1a1a2e;letter-spacing:-0.5px;line-height:1.2;">
                Reset your password
              </h1>
              <p style="margin:0 0 20px;font-size:15px;color:#6b7280;line-height:1.65;">
                Hi {to_name}, we received a request to reset the password for your
                ThinkBreath account.
              </p>
              <p style="margin:0 0 32px;font-size:15px;color:#6b7280;line-height:1.65;">
                Click the button below to choose a new password. This link expires in
                <strong style="color:#374151;">1 hour</strong>.
              </p>

              <!-- CTA button -->
              <table cellpadding="0" cellspacing="0" role="presentation">
                <tr>
                  <td style="border-radius:10px;background:#7c3aed;">
                    <a href="{reset_url}"
                       style="display:inline-block;padding:14px 34px;font-size:15px;
                              font-weight:600;color:#ffffff;text-decoration:none;
                              letter-spacing:0.2px;border-radius:10px;">
                      Reset Password
                    </a>
                  </td>
                </tr>
              </table>

              <!-- URL fallback -->
              <p style="margin:28px 0 0;font-size:12px;color:#9ca3af;line-height:1.7;">
                If the button does not work, copy and paste this link into your browser:
                <br>
                <a href="{reset_url}"
                   style="color:#7c3aed;word-break:break-all;">{reset_url}</a>
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:20px 40px 32px;border-top:1px solid #f3f4f6;">
              <p style="margin:0;font-size:12px;color:#9ca3af;line-height:1.7;">
                If you did not request this, you can safely ignore this email —
                your password will not change.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def send_reset_email(to_email: str, to_name: str, raw_token: str) -> None:
    if not resend.api_key:
        raise HTTPException(
            status_code=500,
            detail="Email service is not configured. Set RESEND_API_KEY in .env",
        )

    reset_url = f"{_FRONTEND_URL}/reset-password?token={raw_token}"

    resend.Emails.send({
        "from":    f"ThinkBreath <{_FROM_EMAIL}>",
        "to":      [to_email],
        "subject": "Reset your ThinkBreath password",
        "html":    _reset_email_html(to_name, reset_url),
    })
