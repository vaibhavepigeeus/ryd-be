import base64
import json
import logging
from typing import Any, Dict, Optional

import jwt
import requests
from decouple import config

logger = logging.getLogger(__name__)


def decode_jwt_header(token: str) -> Dict[str, Any]:
    """
    Decode the Access Token header
    """
    # Split the JWT into its components
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT format")

    # JWT header is the first part (Base64Url encoded)
    header_b64 = parts[0]

    # Add padding to the Base64 string if necessary
    header_b64 += "=" * ((4 - len(header_b64) % 4) % 4)

    # Decode the Base64Url encoded header
    header_json = base64.urlsafe_b64decode(header_b64).decode("utf-8")

    # Parse and return the JSON as a dictionary
    return json.loads(header_json)


def decode_azure_token(access_token: str) -> Dict[str, Any]:
    """
    Validates Azure AD token and returns the decoded token or raises an exception.

    :param access_token: Azure token to validate
    :return: Decoded token if valid
    """
    try:
        logger.info("Starting validation of Azure token.")

        # Extracting ENV Details
        tenant_id = config("AZURE_TENANT_ID")
        client_id = config("AZURE_CLIENT_ID")

        azuread_jwks_uri: str = (
            f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
        )
        token_audience: str = f"api://{client_id}"
        token_issuer: str = f"https://sts.windows.net/{tenant_id}/"

        # Fetch the JWKS (JSON Web Key Set)
        logger.info("Fetching JWKS from %s.", azuread_jwks_uri)
        jwks_response: requests.Response = requests.get(azuread_jwks_uri, timeout=20)
        jwks_response.raise_for_status()  # Check for HTTP errors

        logger.info("Successfully fetched JWKS.")
        jwks: Dict[str, Any] = jwks_response.json()

        public_key_dict = {}
        for jwk in jwks["keys"]:
            kid = jwk["kid"]
            public_key_dict[kid] = {
                "key": jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk)),  # type: ignore
                "issuer": jwk.get("issuer", None),
            }

        # Decode the header to get the kid (Key ID)
        logger.info("Decoding the token header to extract the Key ID (kid).")
        header: Dict[str, Any] = decode_jwt_header(access_token)
        kid = header.get("kid")
        alg = header.get("alg")

        # If the key ID is not found in the JWKS, raise an exception
        if kid not in public_key_dict:
            logger.error("Key ID %s not found in the JWKS.", kid)
            raise jwt.InvalidTokenError("Key ID not found")

        # Retrieve the matching key and issuer
        logger.info("Found matching key for kid: %s.", kid)
        matching_key: Dict[str, Any] = public_key_dict[kid]
        issuer: str = token_issuer or matching_key["issuer"] or ""
        logger.info("Using issuer: %s.", issuer)

        # Decode the token using the public key and verify its claims
        logger.info("Decoding the access token with the public key.")
        decoded_token: Dict[str, Any] = jwt.decode(
            jwt=access_token,
            key=matching_key["key"],
            verify=True,
            algorithms=[alg],  # type: ignore
            audience=token_audience,
            issuer=issuer,
            options={"verify_signature": True, "verify_iss": True, "verify_exp": True},
        )

        logger.info("Token successfully decoded.")
        return decoded_token
    except Exception as e:
        logger.error("Token validation failed: %s", str(e))
        raise e


def generate_azure_token(authorization_code: str, refresh_token:str = None) -> Dict[str, Any]:
    """
    Generates an Azure AD access token using client credentials grant flow.
    :return: The access token response containing the 'access_token' field
    """
    try:
        tenant_id = config("AZURE_TENANT_ID")
        client_id = config("AZURE_CLIENT_ID")
        client_secret = config("AZURE_CLIENT_SECRET")
        redirect_uri = config("AZURE_REDIRECT_URI")
        scope = config("AZURE_SCOPE")

        logger.info("Generating Azure token for tenant %s.", tenant_id)

        # URL to request the token from Azure AD
        url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

        # Prepare the data for the request
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "scope": scope,
            **({
                "grant_type": "authorization_code",
                "code": authorization_code,
            } if not refresh_token else {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            })
        }

        # Set the headers
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        # Make the request to get the token
        logger.info("Requesting token from Azure AD.")
        response = requests.post(
            url, data=data, headers=headers, timeout=20
        )  # default timeout of 20sec

        # Check for request errors
        response.raise_for_status()

        # Log successful token request
        logger.info("Successfully obtained token from Azure AD.")

        # Parse and return the token
        token_response = response.json()
        access_token = token_response.get("access_token")
        refresh_token = token_response.get("refresh_token")

        if not access_token:
            logger.error("Access token not found in response.")
            raise ValueError("Failed to obtain access token.")

        logger.info("Access token successfully retrieved.")
        return {"access_token": access_token,
                "refresh_token": refresh_token
                }

    except Exception as e:
        # Log the error and re-raise it
        logger.error("Error generating token: %s", str(e))
        raise RuntimeError(f"Error generating token: {str(e)}") from e
