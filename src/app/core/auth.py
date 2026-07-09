import jwt
import requests
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from src.app.core.settings import settings

class Auth0JWTBearer:
    def __init__(self):
        self.security = HTTPBearer()
        # Points directly to your unified app configurations
        self.jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
        self._jwks = None

    @property
    def jwks(self):
        """Fetches Auth0 public keys with caching to minimize network overhead."""
        if not self._jwks:
            try:
                self._jwks = requests.get(self.jwks_url, timeout=5).json()
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to fetch authentication keys from provider: {str(e)}"
                )
        return self._jwks

    async def __call__(self, credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())):
        # Fallback security bypass if configuration properties are empty locally
        if not settings.AUTH0_DOMAIN or not settings.AUTH0_AUDIENCE:
            return {"info": "Auth0 skipped - Configuration properties missing from workspace environment."}

        token = credentials.credentials
        try:
            unverified_header = jwt.get_unverified_header(token)
            rsa_key = {}
            for key in self.jwks.get("keys", []):
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
                    audience=settings.AUTH0_AUDIENCE,
                    issuer=f"https://{settings.AUTH0_DOMAIN}/"
                )
                return payload
                
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid or expired credentials token: {str(e)}"
            )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Public key matching signature could not be verified."
        )

# Global singleton dependency instance
auth_required = Auth0JWTBearer()
