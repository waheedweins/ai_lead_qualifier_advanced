import jwt
import requests
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseSettings

class Auth0Settings(BaseSettings):
    AUTH0_DOMAIN: str = "your-tenant.auth0.com"
    AUTH0_AUDIENCE: str = "https://api.yourdomain.com" # Your FastAPI API Identifier

auth0_config = Auth0Settings()

class Auth0JWTBearer:
    def __init__(self):
        self.security = HTTPBearer()
        # Fetch Auth0 public keys dynamically
        jwks_url = f"https://{auth0_config.AUTH0_DOMAIN}/.well-known/jwks.json"
        self.jwks = requests.get(jwks_url).json()

    async def __call__(self, credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())):
        token = credentials.credentials
        try:
            # Extract token header to locate the correct public key
            unverified_header = jwt.get_unverified_header(token)
            rsa_key = {}
            for key in self.jwks["keys"]:
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"]
                    }
            
            if rsa_key:
                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=["RS256"],
                    audience=auth0_config.AUTH0_AUDIENCE,
                    issuer=f"https://{auth0_config.AUTH0_DOMAIN}/"
                )
                return payload # Returns user information payload
                
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid or expired token: {str(e)}"
            )
        
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unable to find appropriate key.")

# Singleton dependency instance
auth_required = Auth0JWTBearer()
