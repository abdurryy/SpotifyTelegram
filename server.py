from flask import Flask, redirect, request, render_template, url_for
import utils.spotify_login as sauth, json, requests, threading

app = Flask(__name__)
token = "6001733099:AAFp-8y4HEmiaE5MeJZyIW3OzEt1xtkaa64"


@app.route('/')
def index():
    return render_template("index.html", telegram_id=request.args.get("id"))

@app.route('/login')
def login():
    response = sauth.getUser()
    return redirect(response)

@app.route('/callback/')
def callback():
    try:
        g = sauth.getUserToken(request.args['code'])
        return render_template("callback.html", access_token=g[0], refresh_token=g[4])
    except Exception as e:return redirect(url_for("error", error=e))

@app.route('/callback/telegram')
def callback_telegram():
    try:
        with open("database.json", "r") as f:
            db = json.load(f)
            telegram_id = request.args.get("id")
            access_token = request.args.get("access_token")
            refresh_token = request.args.get("refresh_token")
            if telegram_id == "None" or access_token == "None":
                return redirect(url_for("error", error="Missing parameters"))
            for user in db["users"]:
                if user["telegram_id"] == telegram_id:
                    user["access_token"] = access_token
                    user["refresh_token"] = refresh_token
                    json.dump(db, open("database.json", "w"), indent=4)
                    requests.get("https://api.telegram.org/bot{}/sendMessage?chat_id={}&text=You have successfully updated your Spotify session!".format(token, telegram_id))
                    return redirect(url_for("success"))
            db["users"].append({"telegram_id": telegram_id, "access_token": access_token, "refresh_token": refresh_token, "queue": [], "current_song":""})
            json.dump(db, open("database.json", "w"), indent=4)
            requests.get("https://api.telegram.org/bot{}/sendMessage?chat_id={}&text=You have successfully logged in to Spotify.".format(token, telegram_id))
            return redirect(url_for("success"))
    except Exception as e:return redirect(url_for("error", error=e))

@app.route('/success')
def success():
    return render_template("success.html")

@app.route('/error')
def error():
    return render_template("error.html", error=request.args.get("error"))

app.run(port=80, host="0.0.0.0")