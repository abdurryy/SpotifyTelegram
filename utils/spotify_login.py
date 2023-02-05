from utils.spotify_auth import getAuth, refreshAuth, getToken

CLIENT_ID = "d2e37bbf421c40ce8f91f85a03274765"
CLIENT_SECRET = ""

PORT = "80"
CALLBACK_URL = "http://139.162.235.83"
SCOPE = "playlist-read-private playlist-read-collaborative user-read-currently-playing playlist-modify-private playlist-modify-public user-read-private"
TOKEN_DATA = []

def getUser():
    return getAuth(CLIENT_ID, "{}:{}/callback/".format(CALLBACK_URL, PORT), SCOPE)

def getUserToken(code):
    global TOKEN_DATA
    TOKEN_DATA = getToken(code, CLIENT_ID, CLIENT_SECRET, "{}:{}/callback/".format(CALLBACK_URL, PORT))
    return TOKEN_DATA

def refreshToken(time):
    time.sleep(time)
    TOKEN_DATA = refreshAuth()

def getAccessToken():
    return TOKEN_DATA