# Setting up HTTPS for the Ollama API

This guide explains how to generate SSL certificates for enabling HTTPS on the Ollama API server.

## Generating Self-Signed Certificates (Development)

For development or testing purposes, you can generate self-signed certificates using OpenSSL:

```bash
# Create directory for certificates
mkdir -p certs

# Generate private key
openssl genrsa -out certs/server.key 2048

# Generate Certificate Signing Request
openssl req -new -key certs/server.key -out certs/server.csr

# Generate self-signed certificate (valid for 365 days)
openssl x509 -req -days 365 -in certs/server.csr -signkey certs/server.key -out certs/server.crt
```

Then, update your `.env` file with the paths to your certificates:

```
SSL_CERT_PATH=certs/server.crt
SSL_KEY_PATH=certs/server.key
```

## Using Let's Encrypt for Production

For production environments, consider using Let's Encrypt to obtain free, trusted SSL certificates:

1. Install Certbot: `pip install certbot`
2. Obtain certificates: `certbot certonly --standalone -d your-domain.com`
3. Update your `.env` file with the paths to the certificates:

```
SSL_CERT_PATH=/etc/letsencrypt/live/your-domain.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/your-domain.com/privkey.pem
```

## Certificate Renewal

Let's Encrypt certificates expire after 90 days. Set up automatic renewal:

```bash
# Add to crontab to check twice daily
echo "0 0,12 * * * python -c 'import random; import time; time.sleep(random.random() * 3600)' && certbot renew -q" | sudo tee -a /etc/crontab > /dev/null
```

## Notes

- Self-signed certificates will cause browsers to show security warnings
- For production use, always use trusted certificates from authorities like Let's Encrypt
- Keep your private keys secure and never commit them to version control