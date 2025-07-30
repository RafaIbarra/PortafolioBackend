# services/email_service.py
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from jinja2 import Template
from datetime import datetime
import dns.resolver
import socket
import smtplib
from email.utils import parseaddr
def verificar_dominio_email(email: str) -> bool:
    try:
        # Extraer dominio
        _, dominio = parseaddr(email)[1].split('@')
        
        # Verificar registros MX del dominio
        try:
            records = dns.resolver.resolve(dominio, 'MX')
            mx_record = str(records[0].exchange)
            return True
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
            return False
        
    except (ValueError, IndexError):
        return False
    
class EmailService:
    def __init__(self):
        # Configuración del servidor SMTP (usa variables de entorno en producción)
        self.smtp_server = "smtp.gmail.com"
        self.port = 587
        self.sender_email = os.getenv("mail", "mytaxesapp@gmail.com")
        self.password = os.getenv("app_pass")  # Usar variables de entorno

    def enviar_correo_html(
        self,
        destinatario: str,
        asunto: str,
        template_html: str,
        contexto: dict
    ) -> bool:
        """
        Envía un correo electrónico con contenido HTML
        
        Args:
            destinatario: Correo del destinatario
            asunto: Asunto del correo
            template_html: Ruta al archivo HTML template
            contexto: Diccionario con variables para el template
            
        Returns:
            bool: True si el envío fue exitoso, False si falló
        """
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg["From"] = self.sender_email
        msg["To"] = destinatario
        msg["Subject"] = asunto
        
        try:
            # Renderizar template HTML
            with open(template_html, 'r', encoding='utf-8') as file:
                template = Template(file.read())
            html_content = template.render(**contexto)
            
            # Crear versiones texto plano y HTML
            text_content = self._html_to_plain_text(html_content)
            
            # Adjuntar ambas versiones
            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Enviar correo
            with smtplib.SMTP(self.smtp_server, self.port) as server:
                server.starttls()
                server.login(self.sender_email, self.password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Error al enviar correo: {e}")
            return False

    def _html_to_plain_text(self, html: str) -> str:
        """Convierte HTML a texto plano (simplificado)"""
        # Esto es una versión simple, considera usar una librería como html2text para producción
        return html.replace('<br>', '\n').replace('<br/>', '\n').replace('</p>', '\n\n')