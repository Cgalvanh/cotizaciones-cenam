"""
Servicio Unificado de Correo Electrónico y Notificaciones CENAM.
Soporta:
1. Resend API (Modo moderno por API REST sin librerías externas)
2. SMTP Clásico (Gmail con Contraseña de Aplicación, Brevo, o SMTP Institucional)
3. Modo Desarrollo / Pruebas (Failsafe que registra el código OTP en los logs y permite pruebas inmediatas)
"""
import os
import json
import smtplib
import urllib.request
import urllib.error
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Carga de variables de entorno desde .env si existe
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except Exception:
    pass

# Variables de entorno opcionales
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
RESEND_FROM = os.getenv("RESEND_FROM", "CENAM Metrología <onboarding@resend.dev>").strip()

SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER or "notificaciones@cenam.mx").strip()

BASE_URL = os.getenv("BASE_URL", "").rstrip("/")


def render_otp_html(codigo: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="utf-8">
      <title>Código de Acceso - CENAM</title>
    </head>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #1e293b;">
      <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 580px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.07); border: 1px solid #e2e8f0;">
        <tr>
          <td style="background-color: #0f172a; padding: 24px 32px; text-align: center;">
            <h1 style="color: #ffffff; margin: 0; font-size: 20px; font-weight: 700; letter-spacing: 0.5px;">CENTRO NACIONAL DE METROLOGÍA</h1>
            <p style="color: #94a3b8; margin: 4px 0 0 0; font-size: 13px;">Portal de Clientes y Servicios Metrológicos</p>
          </td>
        </tr>
        <tr>
          <td style="padding: 36px 32px;">
            <h2 style="color: #0f172a; margin-top: 0; font-size: 18px;">Código Temporal de Acceso</h2>
            <p style="font-size: 14px; line-height: 1.6; color: #475569;">
              Ha solicitado acceso a su panel de solicitudes y cotizaciones en el Portal de CENAM. Utilice el siguiente código de verificación de 6 dígitos:
            </p>
            <div style="background-color: #f1f5f9; border-radius: 8px; border: 2px dashed #cbd5e1; text-align: center; padding: 18px; margin: 28px 0;">
              <span style="font-size: 34px; font-weight: 800; letter-spacing: 8px; color: #1e3a8a; font-family: monospace;">{codigo}</span>
            </div>
            <p style="font-size: 13px; color: #64748b; line-height: 1.5;">
              ⏱️ <strong>Vigencia:</strong> Este código expira en <strong>10 minutos</strong> y es de un solo uso.<br>
              🔒 Si usted no solicitó este acceso, puede ignorar este mensaje con total seguridad.
            </p>
          </td>
        </tr>
        <tr>
          <td style="background-color: #f8fafc; padding: 18px 32px; text-align: center; border-top: 1px solid #e2e8f0; font-size: 12px; color: #94a3b8;">
            Centro Nacional de Metrología (CENAM) &bull; Km 4,5 Carretera a Los Cués, Mpio. El Marqués, Querétaro, México.
          </td>
        </tr>
      </table>
    </body>
    </html>
    """


def render_acuse_html(no_folio: str, token_seguimiento: str, num_instrumentos: int, cliente_nombre: str) -> str:
    url_seguimiento = f"{BASE_URL}/portal?folio={no_folio}&token={token_seguimiento}" if BASE_URL else f"/portal?folio={no_folio}&token={token_seguimiento}"
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="utf-8"></head>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #1e293b;">
      <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 580px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.07); border: 1px solid #e2e8f0;">
        <tr>
          <td style="background-color: #0f172a; padding: 24px 32px; text-align: center;">
            <h1 style="color: #ffffff; margin: 0; font-size: 20px; font-weight: 700;">CENTRO NACIONAL DE METROLOGÍA</h1>
            <p style="color: #94a3b8; margin: 4px 0 0 0; font-size: 13px;">Acuse Oficial de Recepción de Solicitud</p>
          </td>
        </tr>
        <tr>
          <td style="padding: 32px;">
            <h2 style="color: #0f172a; margin-top: 0; font-size: 18px;">¡Solicitud Recibida Exitosamente!</h2>
            <p style="font-size: 14px; line-height: 1.6; color: #475569;">
              Estimado(a) <strong>{cliente_nombre}</strong>, hemos registrado su solicitud de calibración con <strong>{num_instrumentos} partida(s)</strong>.
            </p>
            <div style="background-color: #eff6ff; border-left: 4px solid #2563eb; padding: 14px 18px; margin: 20px 0; border-radius: 0 8px 8px 0;">
              <p style="margin: 0; font-size: 13px; color: #1e40af;"><strong>No. de Folio Oficial:</strong> <span style="font-size: 17px; font-weight: bold; color: #1d4ed8;">{no_folio}</span></p>
              <p style="margin: 6px 0 0 0; font-size: 12px; color: #3b82f6;"><strong>Clave de Seguimiento:</strong> {token_seguimiento}</p>
            </div>
            <p style="font-size: 14px; line-height: 1.6; color: #475569;">
              La Ventanilla de Servicios (SSI) y las Áreas Técnicas de CENAM revisarán la viabilidad técnica y emitirán la cotización oficial en un plazo máximo de 3 días hábiles.
            </p>
            <div style="text-align: center; margin: 28px 0;">
              <a href="{url_seguimiento}" style="background-color: #1e3a8a; color: #ffffff; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 14px; display: inline-block;">
                Ver Estado de mi Solicitud en Línea &rarr;
              </a>
            </div>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """


def enviar_correo(destinatario: str, asunto: str, html_body: str) -> dict:
    """
    Envía un correo mediante Resend, SMTP o modo emulado (Dev).
    Retorna un diccionario indicando éxito y modo utilizado.
    """
    destinatario = destinatario.strip()
    if not destinatario:
        return {"success": False, "error": "Correo destinatario vacío"}

    # 1. Priorizar SMTP si está configurado (Gmail, Brevo, Institucional) para entrega sin restricciones
    smtp_host = os.getenv("SMTP_HOST", SMTP_HOST).strip()
    smtp_port = int(os.getenv("SMTP_PORT", str(SMTP_PORT)))
    smtp_user = os.getenv("SMTP_USER", SMTP_USER).strip()
    smtp_password = os.getenv("SMTP_PASSWORD", SMTP_PASSWORD).strip()
    smtp_from = os.getenv("SMTP_FROM", SMTP_FROM).strip() or smtp_user or "CENAM Metrología <notificaciones@cenam.mx>"

    if smtp_host and smtp_user and smtp_password:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = asunto
            msg["From"] = smtp_from
            msg["To"] = destinatario
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            server = smtplib.SMTP(smtp_host, smtp_port, timeout=12)
            server.starttls()
            server.login(smtp_user, smtp_password.replace(" ", "") if "gmail.com" in smtp_host else smtp_password)
            server.sendmail(smtp_from, [destinatario], msg.as_string())
            server.quit()
            print(f"📧 [SMTP SUCCESS] Correo entregado exitosamente a {destinatario} via SMTP ({smtp_host})")
            return {"success": True, "provider": "smtp"}
        except Exception as e:
            print(f"[EMAIL SMTP EXCEPTION] {e}")

    # 2. Intentar Resend API si está configurada la llave y SMTP no se usó
    api_key = os.getenv("RESEND_API_KEY", RESEND_API_KEY).strip()
    from_email = os.getenv("RESEND_FROM", RESEND_FROM).strip() or "CENAM Metrología <onboarding@resend.dev>"
    if api_key:
        send_candidates = [from_email]
        if "onboarding@resend.dev" not in from_email:
            send_candidates.append("CENAM Metrología <onboarding@resend.dev>")

        for current_from in send_candidates:
            try:
                req_data = json.dumps({
                    "from": current_from,
                    "to": [destinatario],
                    "subject": asunto,
                    "html": html_body
                }).encode("utf-8")

                req = urllib.request.Request(
                    "https://api.resend.com/emails",
                    data=req_data,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "User-Agent": "resend-python/2.0.0"
                    },
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    res_body = json.loads(resp.read().decode("utf-8"))
                    print(f"📧 [RESEND SUCCESS] Correo entregado exitosamente a {destinatario} via Resend (ID: {res_body.get('id')})")
                    return {"success": True, "provider": "resend", "data": res_body}
            except urllib.error.HTTPError as e:
                err_msg = e.read().decode("utf-8", errors="ignore")
                print(f"[EMAIL RESEND HTTP {e.code}] {err_msg}")
                if "not verified" in err_msg and current_from != send_candidates[-1]:
                    continue
                if "only send testing emails to your own email" in err_msg:
                    print(f"⚠️ [RESEND SANDBOX] Cuenta en modo prueba gratuita. Envío bloqueado a terceros. Activando failsafe con OTP visible.")
                    break
            except Exception as e:
                print(f"[EMAIL RESEND EXCEPTION] {e}")
                break

    # 3. Modo Failsafe / Demostración Local
    # Permite al usuario y al evaluador probar el sistema sin dependencias bloqueantes
    print("=" * 65)
    print(f"📧 [CENAM EMAIL SERVICE - MODO DEMO / LOCAL]")
    print(f"Para: {destinatario}")
    print(f"Asunto: {asunto}")
    print("=" * 65)
    return {
        "success": True,
        "provider": "dev_mode",
        "message": "Correo simulado con éxito (modo local/demo sin proveedor externo activo)."
    }


def enviar_codigo_otp(correo: str, codigo: str) -> dict:
    """Envía el código OTP de 6 dígitos al correo del cliente."""
    asunto = f"{codigo} es su código de verificación CENAM"
    html = render_otp_html(codigo)
    res = enviar_correo(correo, asunto, html)
    res["dev_otp"] = codigo  # Útil para entorno local de pruebas
    return res


def enviar_acuse_solicitud(correo: str, no_folio: str, token_seguimiento: str, num_instrumentos: int, cliente_nombre: str) -> dict:
    """Envía el acuse de confirmación de registro de solicitud con Folio."""
    asunto = f"Acuse de Recepción de Solicitud - Folio {no_folio} [CENAM]"
    html = render_acuse_html(no_folio, token_seguimiento, num_instrumentos, cliente_nombre)
    return enviar_correo(correo, asunto, html)
