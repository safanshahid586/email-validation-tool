from email_validator import validate_email, EmailNotValidError
import dns.resolver
import smtplib
import time
import socket
import subprocess

# Email syntax validation using email-validator
def is_valid_syntax(email):
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False

# DNS resolver configuration with increased timeout and multiple DNS servers
def get_dns_resolver():
    resolver = dns.resolver.Resolver()
    resolver.lifetime = 10  # Increase the timeout to 10 seconds
    resolver.timeout = 5  # Set individual request timeout to 5 seconds
    resolver.nameservers = [
        '8.8.8.8',  # Google DNS
        '8.8.4.4',  # Google DNS
        '1.1.1.1',  # Cloudflare DNS
        '1.0.0.1',  # Cloudflare DNS
    ]
    return resolver

# Domain validation using the custom resolver
def validate_domain(domain, resolver):
    try:
        resolver.resolve(domain, 'MX')
        return True
    except dns.resolver.NoAnswer:
        return False
    except dns.resolver.NXDOMAIN:
        return False
    except dns.resolver.Timeout:
        print(f"DNS query timed out while resolving {domain}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

# Check for MX records using the custom resolver
def check_mx_records(domain, resolver):
    try:
        mx_records = resolver.resolve(domain, 'MX')
        return mx_records
    except dns.resolver.NoAnswer:
        return None
    except dns.resolver.NXDOMAIN:
        return None
    except dns.resolver.Timeout:
        print(f"DNS query timed out while checking MX records for {domain}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# Fallback to using nslookup for DNS resolution
def fallback_nslookup(domain):
    try:
        result = subprocess.run(['nslookup', '-type=MX', domain], capture_output=True, text=True)
        if "mail exchanger" in result.stdout:
            return True
        else:
            print(f"nslookup did not find any MX records for {domain}.")
            return False
    except Exception as e:
        print(f"nslookup failed with error: {e}")
        return False

# SMTP validation to check if the email exists with retry mechanism
def smtp_validation(email, retries=3, delay=5):
    try:
        domain = email.split('@')[1]
        resolver = get_dns_resolver()
        mx_records = check_mx_records(domain, resolver)
        if not mx_records:
            # Attempt fallback with nslookup
            if fallback_nslookup(domain):
                print("MX records found via nslookup.")
            else:
                print(f"Result: The email '{email}' is invalid because no MX records were found.")
                return False

        # SMTP connection and validation
        mx_record = mx_records[0].exchange.to_text() if mx_records else None
        if mx_record:
            server = smtplib.SMTP(timeout=60)  # Increased SMTP connection timeout to 60 seconds
            server.connect(mx_record)
            server.helo('yourdomain.com')  # Replace with your server's domain
            server.mail('test@domain.com')
            code, message = server.rcpt(email)
            server.quit()
            return code == 250
        return False
    except smtplib.SMTPServerDisconnected as e:
        print(f"SMTP validation error (disconnected): {e}")
        if retries > 0:
            print(f"Retrying... ({retries} attempts left)")
            time.sleep(delay)
            return smtp_validation(email, retries=retries-1, delay=delay)
        return False
    except Exception as e:
        print(f"SMTP validation error: {e}")
        if retries > 0:
            print(f"Retrying... ({retries} attempts left)")
            time.sleep(delay)
            return smtp_validation(email, retries=retries-1, delay=delay)
        return False

# Function to validate an email address
def validate_email_address(email):
    if not is_valid_syntax(email):
        return f"Result: The email '{email}' is invalid due to incorrect syntax."
    
    domain = email.split('@')[1]
    resolver = get_dns_resolver()

    if not validate_domain(domain, resolver):
        return f"Result: The email '{email}' is invalid due to an invalid domain."
    elif not check_mx_records(domain, resolver) and not fallback_nslookup(domain):
        return f"Result: The email '{email}' is invalid due to no MX records found."
    elif not smtp_validation(email):
        return f"Result: The email '{email}' is invalid because SMTP validation failed."
    else:
        return f"Result: The email '{email}' is valid and ready to use."

