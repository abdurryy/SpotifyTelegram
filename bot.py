import telebot, json,requests, base64, asyncio
import utils.spotify_auth as spotify_auth
import utils.spotify_login as spotify_login
from utils.spotify_download import SpotifyDownload as spotify_download
import random

token = "6001733099:AAFp-8y4HEmiaE5MeJZyIW3OzEt1xtkaa64"
bot = telebot.TeleBot(token, parse_mode=None)
url = "http://localhost:5000"

bot.set_my_commands([telebot.types.BotCommand("menu", "Start the bot"), telebot.types.BotCommand("help", "Get help")])


def get_access_token(id, message):
    with open("database.json", "r") as f:
        db = json.load(f)
        for user in db["users"]:
            if str(user["telegram_id"]) == str(id):
                r = requests.get("https://api.spotify.com/v1/me", headers={"Authorization": "Bearer " + user["access_token"]})
                if r.status_code == 200:
                    return user["access_token"]
                else:
                    if r.status_code != 429:
                        x = re_login(message, user["telegram_id"], user["refresh_token"])
                        if x == True:
                            with open("database.json", "r") as r:
                                db = json.load(r)
                                for user in db["users"]:
                                    if str(user["telegram_id"]) == str(id):
                                        return user["access_token"]
                        else:
                            return bot.send_message(message.chat.id, "We were unable to refresh your access token. Please login again.")
                    else:
                        return bot.send_message(message.chat.id, "You have been rate limited by Spotify. Please try again later.")
        bot.send_message(message.chat.id, f"You need to login to Spotify to use this bot. {url}/?id={id}", 
            reply_markup=telebot.util.quick_markup({
                'Login via Spotify': {'url': f"https://twitter.com"}
            })
        )
        return None

def re_login(message, telegram_id, refresh_token):
    body = {
        "grant_type" : "refresh_token",
        "refresh_token" : refresh_token,
    }
    encoded = base64.b64encode("{}:{}".format(spotify_login.CLIENT_ID, spotify_login.CLIENT_SECRET).encode('utf-8')).decode('utf-8')
    headers = {"Authorization" : "Basic {}".format(encoded)} 
    r = requests.post("https://accounts.spotify.com/api/token", data=body, headers=headers)
    with open("database.json","r") as f:
        db = json.load(f)
        for user in db["users"]:
            if str(user["telegram_id"]) == str(telegram_id):
                user["access_token"] = r.json()["access_token"]
                with open("database.json","w") as f:
                    json.dump(db, f, indent=4)
                return True

def get_info(access_token, message):
    try:
        r = requests.get("https://api.spotify.com/v1/me", headers={"Authorization": "Bearer " + access_token})
        return (r["id"], r["display_name"])
    except:
        print(r.json()["error"]["message"])
        re_login(message)
        return None

objs = []
def hide(obj):
    r = str(random.randint(100000,999999))
    objs.append({"id": r, "obj": obj})
    return r

def show(id):
    for obj in objs:
        if obj["id"] == id:
            return obj["obj"]

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    type = call.data.split(":")[0]
    value = call.data.split(":")[1]
    access_token = get_access_token(call.from_user.id, call.message)
    if type == "playlist":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        xs = bot.send_message(call.message.chat.id, "Preparing playlist...")
        r = requests.get(f"https://api.spotify.com/v1/playlists/{value}/tracks",
            headers={"Authorization": "Bearer " + access_token}
        )
        markup = {}        
        for i in r.json()["items"]:
            # i["track"]["artists"][0]["name"]+" "+str(i["track"]["duration_ms"])+" "+i["track"]["id"]+" "+i["track"]["name"]
            with open("database.json", "r") as f:
                db = json.load(f)
                for user in db["users"]:
                    if str(user["telegram_id"]) == str(call.from_user.id):
                        if f'{i["track"]["artists"][0]["name"]} - {i["track"]["name"]}' not in user["queue"]:
                            # install song
                            spotify_download.download(f'{i["track"]["artists"][0]["name"]} - {i["track"]["name"]}')
                            markup[f'{i["track"]["artists"][0]["name"]} - {i["track"]["name"]}'] = {
                                "callback_data": f'queue:{i["track"]["artists"][0]["name"]} - {i["track"]["name"]}:'+str(value) # add to queue f'{i["track"]["artists"][0]["name"]} - {i["track"]["name"]}'
                            }
                        else:
                            markup[f'(in queue) {i["track"]["artists"][0]["name"]} - {i["track"]["name"]}'] = {
                                "callback_data": "already:" # add to queue f'{i["track"]["artists"][0]["name"]} - {i["track"]["name"]}'
                            }
        bot.delete_message(call.message.chat.id, xs.message_id)
        markup = telebot.util.quick_markup(markup, row_width=5)
        bot.send_message(call.message.chat.id, "Would you like to add any of these songs to your queue?", reply_markup=markup)
    elif type == "queue":
        with open("database.json", "r") as f:
            db = json.load(f)
            for user in db["users"]:
                if str(user["telegram_id"]) == str(call.from_user.id):
                    if value not in user["queue"]:
                        user["queue"].append(value)
                        with open("database.json", "w") as f:
                            json.dump(db, f, indent=4)
                        bot.answer_callback_query(call.id, "Added to queue!")
                    else:
                        bot.answer_callback_query(call.id, "This song is already in your queue!")
        #file = asyncio.run(spotify_download.download(value['current']))
        #bot.send_audio(call.message.chat.id, open(file, 'rb'), reply_markup=markup)
    elif type == "unqueue":
        with open("database.json", "r") as f:
            db = json.load(f)
            for user in db["users"]:
                if str(user["telegram_id"]) == str(call.from_user.id):
                    if value in user["queue"]:
                        user["queue"].remove(value)
                        with open("database.json", "w") as f:
                            json.dump(db, f, indent=4)
                        bot.answer_callback_query(call.id, "Removed from queue!")
            bot.answer_callback_query(call.id, "This song is not in your queue!")
    elif type == "already":
        bot.answer_callback_query(call.id, "This song is already in your queue!")
    elif type == "interaction":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "Alright, let's do this!")
        if value == "playlists":
            r = requests.get("https://api.spotify.com/v1/me/playlists", headers={"Authorization": "Bearer " + access_token})
            playlists = r.json()["items"]
            markup = {}
            for playlist in playlists: 
                markup[playlist["name"]] = {"callback_data": f"playlist:{playlist['id']}"}
            markup = telebot.util.quick_markup(markup, row_width=1)
            bot.send_message(call.message.chat.id, "Fair enough, here goes your playlists! Which one do are feeling for today?", reply_markup=markup)
        elif value == "queue":
            with open("database.json", "r") as f:
                db = json.load(f)
                for user in db["users"]:
                    if str(user["telegram_id"]) == str(call.from_user.id):
                        markup = {}
                        if len(user["queue"]) == 0:
                            bot.send_message(call.message.chat.id, "Your queue is empty! Add some songs to your queue first!")
                        for song in user["queue"]:
                            markup[song] = {"callback_data": f"unqueue:{song}"}
                        markup = telebot.util.quick_markup(markup, row_width=5)
                        bot.send_message(call.message.chat.id, "Here goes your queue! Click to remove any song from your queue.", reply_markup=markup)
        elif value == "play":
            # remove all bot message from chat
            with open("database.json", "r") as f:
                db = json.load(f)
                found = False
                for store in db["chats"]:
                    if store["chat_id"] == call.message.chat.id:
                        found = True
                        for message in store["m_ids"]:
                            bot.delete_message(call.message.chat.id, message)
                        store["m_ids"] = []
                        with open("database.json", "w") as f:
                            json.dump(db, f, indent=4)
                if not found:
                    db["chats"].append({"chat_id": call.message.chat.id, "m_ids": []})
                    with open("database.json", "w") as f:
                        json.dump(db, f, indent=4)
                    
                for user in db["users"]:
                    if str(user["telegram_id"]) == str(call.from_user.id):
                        if len(user["queue"]) > 0:
                            for song in user["queue"]:
                                file = spotify_download.download(song)
                                l = bot.send_audio(call.message.chat.id, open(file, 'rb'))
                                for store in db["chats"]:
                                    if store["chat_id"] == call.message.chat.id:
                                        store["m_ids"].append(l.message_id)
                                with open("database.json", "w") as f:
                                    json.dump(db, f, indent=4)
                            """markup = telebot.util.quick_markup({
                                "Next": {"callback_data": "interaction:play:next"},
                                "Previous": {"callback_data": "interaction:play:previous"},
                                "Stop": {"callback_data": "interaction:stop"},
                            })"""
                        else:
                            bot.send_message(call.message.chat.id, "Your queue is empty! Add some songs to your queue first!")

@bot.message_handler(func=lambda message: True, commands=["menu"])
def menu(message):
    if get_access_token(message.from_user.id, message) == None:return
    markup = telebot.util.quick_markup({
        "Playlists": {"callback_data": "interaction:playlists"},
        "Queue": {"callback_data": "interaction:queue"},
        "Play": {"callback_data": "interaction:play"},
    }, row_width=2)
    # make inline keyboard
    bot.send_message(message.chat.id, "What do you feel like to do?", reply_markup=markup)

@bot.message_handler(func=lambda message: True, commands=["vc"])
def vc(message):
    bot.send_audio(message.chat.id, open("songs/Ashe - Moral Of The Story (Lyrics).mp3", 'rb'), title="Ashe - Moral Of The Story")
    
            

bot.infinity_polling()