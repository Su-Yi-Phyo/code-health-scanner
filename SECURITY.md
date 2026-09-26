@"
# Security Policy

## Reporting a Security Issue

If you discover a security issue in CodePulse, please report it privately to the project team rather than opening a public issue containing sensitive information.

## Secrets and Credentials

CodePulse uses environment variables for sensitive configuration.

Never commit:

- IBM Bob API keys
- Access tokens
- Passwords
- `.env` files containing real credentials
- Private configuration or authentication data

Use `.env.example` as a reference for required environment variables.

## IBM Bob

The `BOB_API_KEY` must be configured as an environment variable and must never be exposed in frontend code or committed to the repository.
"@ | Set-Content SECURITY.MD