import secrets
import base64
import hashlib
import urllib.parse
import webbrowser
import requests

# This code comes from this github link, all credit to them
# TYSM FOR MAKING IT!!!!!
# https://github.com/RomeoDespres/pkce/

def generate_code_verifier(length: int = 128) -> str:
    """Return a random PKCE-compliant code verifier.

    Parameters
    ----------
    length : int
        Code verifier length. Must verify `43 <= length <= 128`.

    Returns
    -------
    code_verifier : str
        Code verifier.

    Raises
    ------
    ValueError
        When `43 <= length <= 128` is not verified.
    """
    if not 43 <= length <= 128:
        msg = 'Parameter `length` must verify `43 <= length <= 128`.'
        raise ValueError(msg)
    code_verifier = secrets.token_urlsafe(96)[:length]
    return code_verifier

def generate_pkce_pair(code_verifier_length: int = 128) -> tuple[str, str]:
    """Return random PKCE-compliant code verifier and code challenge.

    Parameters
    ----------
    code_verifier_length : int
        Code verifier length. Must verify
        `43 <= code_verifier_length <= 128`.

    Returns
    -------
    code_verifier : str
    code_challenge : str

    Raises
    ------
    ValueError
        When `43 <= code_verifier_length <= 128` is not verified.
    """
    if not 43 <= code_verifier_length <= 128:
        msg = 'Parameter `code_verifier_length` must verify '
        msg += '`43 <= code_verifier_length <= 128`.'
        raise ValueError(msg)
    code_verifier = generate_code_verifier(code_verifier_length)
    code_challenge = get_code_challenge(code_verifier)
    return code_verifier, code_challenge

def get_code_challenge(code_verifier: str) -> str:
    """Return the PKCE-compliant code challenge for a given verifier.

    Parameters
    ----------
    code_verifier : str
        Code verifier. Must verify `43 <= len(code_verifier) <= 128`.

    Returns
    -------
    code_challenge : str
        Code challenge that corresponds to the input code verifier.

    Raises
    ------
    ValueError
        When `43 <= len(code_verifier) <= 128` is not verified.
    """
    if not 43 <= len(code_verifier) <= 128:
        msg = 'Parameter `code_verifier` must verify '
        msg += '`43 <= len(code_verifier) <= 128`.'
        raise ValueError(msg)
    hashed = hashlib.sha256(code_verifier.encode('ascii')).digest()
    encoded = base64.urlsafe_b64encode(hashed)
    code_challenge = encoded.decode('ascii')[:-1]
    return code_challenge

CLIENT_ID = '2cd97920621941218d924b9c6ccca02d'
redirect_uri = 'http://localhost:8888'

def promptUserForAuth(scopes: str):
    codeVerifier, codeChallenge = generate_pkce_pair()

    state = secrets.token_urlsafe()

    queryParams = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'code_challenge_method': 'S256',
        'state': state,
        'scope': scopes,
        'code_challenge': codeChallenge
    }

    webbrowser.open(r"https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(queryParams))
    return state, codeVerifier

def authenticateUser(url, state, codeVerifier):
    params = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(params.query)

    if state != query['state'][0]:
        print('Error, states do not match!')
        return

    if 'code' in query.keys():
        code = query['code'][0]
    elif 'error' in query.keys():
        print(f"Error, {query['error']}!")
        return

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    body = {
        "client_id": CLIENT_ID,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "code_verifier": codeVerifier
    }

    tokenReq = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=body)
    
    if tokenReq.status_code == 200:
        accessToken = tokenReq.json()['access_token']
        refreshToken = tokenReq.json()['refresh_token']
    else:
        print(f"Error, status code {tokenReq.status_code}")
        print(tokenReq.json())
        return

    return accessToken, refreshToken