import jwt
import requests
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from src.app.core.settings import settings  # Securely imports your clean settings object

class Auth0JWTBearer:
    def __init__(self):
        self.security = HTTPBearer()
        self.jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
        self._jwks = None

    @property
    def jwks(self):
        """Lazy load JSON Web Key Sets from Auth0 to verify signatures."""
        if not self._jwks:
            try:
                self._jwks = requests.get(self.jwks_url, timeout=5).json()
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to fetch verification keys from security provider: {str(e)}"
                )
        return self._jwks

    async def __call__(self, credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())):
        # Safe structural bypass check if configuration properties are empty
        if not settings.AUTH0_DOMAIN or not settings.AUTH0_AUDIENCE:
            return {"info": "Auth0 security skipped - variables missing from runtime workspace environment."}

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
                detail=f"Invalid or expired security token credentials: {str(e)}"
            )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Public signatures could not be verified against authentication keys."
        )

# Global authorization dependency initialization hook
auth_required = Auth0JWTBearer()
