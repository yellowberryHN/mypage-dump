import os, requests, re, time, codecs, jsons
from fastapi import FastAPI, Form, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, Response, HTMLResponse, FileResponse
from jsmin import jsmin
from bs4 import BeautifulSoup
from user_agent import generate_user_agent

# time stuff
from datetime import datetime
import pytz

"""

Left to implement:
- stage up
- friends
- titles
- navs
- trophies
- boxes
- total high score (added up all of scores?)
- special song unlocks [/music/unlock]
- gates

"""

endpoint = os.environ.get("MYPAGE_ENDPOINT")
endpoint = endpoint if endpoint is not None else ""

jst = pytz.timezone("Asia/Tokyo") # used for time conversion
magic = codecs.decode("nvzrVq","rot-13") # hi sega
full_dump = True # dump play count

difficulty_dict = {
    "NORMAL": 0,
    "HARD": 1,
    "EXPERT": 2,
    "INFERNO": 3
}

def get_int(string):
    return int(re.search(r'(\d+)', string).group(1))

class DifficultyStats:
    def __init__(self, score, rating, achieve, play_count):
        self.score = score
        self.rating = rating
        self.achieve = achieve
        self.play_count = play_count

class BasicDifficultyStats:
    def __init__(self, score, rating, achieve):
        self.score = score
        self.rating = rating
        self.achieve = achieve

class Progress:
    def __init__(self, bests_total, bests_completed) -> None:
        self.bests_total =  bests_total
        self.bests_completed = bests_completed

class Song:
    def __init__(self, id, name):
        self.id = id
        self.__name = name

class PersonalBest(Song):
    def __init__(self, id, name):
        self.id = id
        self.__name = name
        self.difficulties = []
        self.play_count = 0

class RecentPlay(Song):
    def __init__(self, id, name, timestamp, difficulty, judgements, timings, max_combo):
        self.id = id 
        self.__name = name
        self.timestamp = timestamp
        self.difficulty = difficulty
        self.judgements = judgements
        self.timings = timings
        self.max_combo = max_combo

class Settings: 
    def __init__(self, game, display, design, sound):
        self.game = game
        self.display = display
        self.design = design
        self.sound = sound




class User:
    # for internal use
    __songs_total = 0
    __ua = generate_user_agent(navigator="chrome",device_type=("smartphone","desktop"))
    __headers_form_encoded = {"Content-Type": "application/x-www-form-urlencoded"} 

    name = ""
    songs = []
    recents = []

    def login_request(self):
        print("Logging in with user ID {0}...".format(self.id))
        print(f"Using user agent: '{self.__ua}'")
        self.__response = requests.request("POST", f"{endpoint}/login/exec", data = "{0}={1}".format(magic, self.id), headers=self.__headers_form_encoded | {"User-Agent": self.__ua})
        
    def gen_cookie(self):
        if "Set-Cookie" in self.__response.headers:
            self.__wsid = re.search(r'WSID=(\w+);', self.__response.headers["Set-Cookie"]).group(1)
            #print("gen_cookie(): new cookie '{0}'".format(self.__wsid))
            return {"User-Agent": self.__ua, "Cookie": "WSID={0}; WUID={0}".format(self.__wsid)}
        else:
            print("User got logged out...")
            self.login_request()

    def get_user_info(self):
        print("Getting player info...")
        self.__response = requests.request("GET", f"{endpoint}/player", headers=self.gen_cookie())

        soup = BeautifulSoup(self.__response.text, 'lxml')

        self.name = soup.select_one('.user-info__detail__name').text
        self.title = soup.select_one('.user-info__detail__title').text
        self.level = get_int(soup.select_one('.user-info__detail__lv > span').text)
        self.rate = int(soup.select_one('.rating__data').text)

        stage = soup.select_one('.user-info__icon__stage img')
        if stage:
            tmp = re.search(r'stage_icon_(\d+)_(\d).png', stage["src"])
            self.emblem = {"stage": int(tmp.group(1)), "type": int(tmp.group(2))}

        pointlist = soup.select(".poss-wp")
        self.points = get_int(soup.select_one('.user-info__detail__wp').text)
        self.lifetime_points = get_int(soup.select_one('dl.poss-wp__detail:nth-child(2) > dd:nth-child(1)').text)
        self.used_points = get_int(soup.select_one('dl.poss-wp__detail:nth-child(3) > dd:nth-child(2)').text)
        
        self.ex_tickets = int(soup.select_one('.user-info__detail__ex').text)
        self.icon = get_int(soup.select_one('.icon__image > img')["src"])
        self.color = get_int(soup.select_one('.symbol__color__base > img')["src"])

        self.__songs_total = int(soup.select_one('span.score-point__difficulty.difficulty__normal').text)

    def get_song_data(self):
        print("Getting song list...")
        self.__response = requests.request("GET", f"{endpoint}/music", headers=self.gen_cookie())
        
        soup = BeautifulSoup(self.__response.text, 'lxml')
        
        # Get song data from song list
        songlist = soup.select(".playdata__score-list__wrap li.item", limit=self.__songs_total)

        print("Getting favorites...")
        self.favorites = []
        favlist = soup.select(".playdata__score-list__wrap li.item.filter-favorite")
        for element in favlist:
            self.favorites.append(int(element.div.form.input["value"]))

        if full_dump:
            print("Getting song data for {0} songs...".format(self.__songs_total))
            for song in songlist:
                yeah = PersonalBest(int(song.div.form.input["value"]), song.div.a.div.div.text)
                self.songs.append(self.scrape_song_data(yeah))
        else:
            print("Getting song data for {0} songs [LITE]...".format(self.__songs_total))
            for song in songlist:
                yeah = PersonalBest(int(song.div.form.input["value"]), song.div.a.div.div.text)

                diffs = ["normal", "hard", "expert", "inferno"]

                for diff in diffs:
                    score = get_int(song.select_one(f".song-info__bottom-wrap.difficulty__{diff} .playdata__score-list__song-info__score").text)

                    # difficulty rate and achieve
                    icons = song.select(f".playdata__score-list__icon.score__icon__{diff} > div")

                    temp_rate = icons[0].img["src"].replace("/img/web/music/rate_icon/", "").split(".")[0]
                    rate = 0

                    if temp_rate.startswith("rate_"):
                        rate = int(temp_rate.split("_")[1])
                        
                    temp_achieve = icons[1].img["src"].replace("/img/web/music/achieve_icon/", "").split(".")[0]
                    achieve = 0

                    if temp_achieve.startswith("achieve"):
                        achieve = int(temp_achieve.replace("achieve",""))

                    yeah.difficulties.append(BasicDifficultyStats(score, rate, achieve))

                self.songs.append(yeah)

    def scrape_song_data(self, song):
        print(f"* <{song.id}> ", end='')
        self.__response = requests.request("POST", f"{endpoint}/music/detail", data = f"musicId={song.id}", headers=self.__headers_form_encoded | self.gen_cookie())
        
        soup = BeautifulSoup(self.__response.text, 'lxml')
        song.play_count = get_int(soup.select_one(".song-info__play-count > span").text)
        song.difficulties = [] # WHY THE FUCK IS THIS REQUIRED
    
        # Selector for difficulties
        diffs = soup.select(".score-detail__list__song-info")

        for diff in diffs:
            play_count = get_int(diff.select_one(".song-info__top__play-count").text)
            score = get_int(diff.select_one(".song-info__score").text)
            
            # difficulty name
            # print(diff.select_one(".song-info__top__lv > div").text)
            
            # difficulty rate and achieve
            icons = diff.select(".score-detail__icon > div > img")

            temp_rate = icons[0]["src"].replace("/img/web/music/rate_icon/", "").split(".")[0]
            rate = 0

            if temp_rate.startswith("rate_"):
                rate = int(temp_rate.split("_")[1])
                
            temp_achieve = icons[1]["src"].replace("/img/web/music/achieve_icon/", "").split(".")[0]
            achieve = 0

            if temp_achieve.startswith("achieve"):
                achieve = int(temp_achieve.replace("achieve",""))

            diff_stats = DifficultyStats(score, rate, achieve, play_count)
            print(diff_stats.__dict__)
            song.difficulties.append(diff_stats)
         
        print("({0} diffs)".format(len(song.difficulties))) # mark song as done
        return song

    def get_recent_plays(self):
        print("Getting recent plays...")
        self.__response = requests.request("GET", f"{endpoint}/history", headers=self.gen_cookie())

        soup = BeautifulSoup(self.__response.text, 'lxml')

        # Get song data from song list
        recentlist = soup.select(".playdata__history-list__wrap > li")
        for song in recentlist:
            # play time
            time = song.select_one(".playdata__history-list__song-info__top")
            time.span.decompose()
            timestamp = jst.localize(datetime.strptime(time.text,'%Y/%m/%d %H:%M:%S')).astimezone(pytz.utc)
            #print(timestamp)

            name = song.select_one(".playdata__history-list__song-info__name").text
            song_id = song.select_one("#musicId")["value"]

            diff = difficulty_dict[song.select_one(".playdata__history-list__song-info__lv").text.split(" ")[0]]

            row_elements = song.select(".playdata__detail-table > li", limit=7)
            judgements = []
            for row in range(4):
                judgements.append(int(row_elements[row].select_one(".detail-table__score").text))
            timings = []
            for row in range(4,6):
                timings.append(int(row_elements[row].select_one(".detail-table__score").text))
                
            max_combo = int(song.select_one(".detail-table__score.combo .combo__num").text)

            recent = RecentPlay(song_id, name, timestamp, diff, judgements, timings, max_combo)
        
            self.recents.append(recent)

    def get_icons(self):
        print("Getting unlocked icons...")
        self.__response = requests.request("GET", f"{endpoint}/icon", headers=self.gen_cookie())
        soup = BeautifulSoup(self.__response.text, 'lxml')

        self.icons = []
        icon_elements = soup.select(".collection__icon-list .item")
        for icon in icon_elements:
            self.icons.append(int(icon["data-icon_id"]))

    def get_plates(self):
        print("Getting unlocked plates...")
        self.__response = requests.request("GET", f"{endpoint}/plate", headers=self.gen_cookie())
        soup = BeautifulSoup(self.__response.text, 'lxml')

        self.plate = get_int(soup.select_one(".current-icon__icon").img["src"])

        self.plates = []
        plate_elements = soup.select(".collection__nameplate-list .nameplate_item")
        for plate in plate_elements:
            self.plates.append(int(plate["data-nameplate_id"]))

    def get_settings(self):
        print("Getting settings...")

        game_settings = {
            "noteSpeed": None, 
            "judgeLineTiming": None, 
            "mask": None, 
            "movie": None, 
            "bonusNoteEffect": None, 
            "mirror": None, 
            "giveup": None
        }

        display_settings = {
            "judgePosition": None,
            "judgeDetail": None,
            "informationMask": None, 
            "guideLineInterval": None, 
            "guideLineMask": None, 
            "guideMeasureLine": None, 
            "centerDisplay": None,
            "scoreDisplay": None,
            "multiRankDisplay": None,
            "emblemDisplay": None,
            "rateDisplay": None,
            "playerLevelDisplay": None,
            "gateDirectingSkip": None,
            "missionDirectingSkip": None
        }

        design_settings = {
            "myColor": {
                "current": None,
                "unlocked": []
            },
            "noteWidth": None,
            "touchNoteColor": None,
            "chainNoteColor": None,
            "slideNoteLeftColor": None,
            "slideNoteRightColor": None,
            "snapNoteUpColor": None,
            "snapNoteDownColor": None,
            "holdNoteColor": None,
            "slideColorInvert": None,
            "touchEffectPop": None,
            "touchEffectShoot": None,
            "keyBeam": None,
            "rNoteEffect": None
        }

        sound_settings = {
            "noteTouchSe": None,
            "bgmVolume": None,
            "guideSoundVolume": None,
            "touchNoteVolume": None,
            "holdNoteVolume": None,
            "slideNoteVolume": None,
            "snapNoteVolume": None,
            "chainNoteVolume": None,
            "bonusNoteVolume": None,
            "charaSound": None,
            "rNoteVolume": None
        }

        print("* Game...")

        for setting in game_settings:
            self.__response = requests.request("GET", f"{endpoint}/option/{setting}", headers=self.gen_cookie())
            soup = BeautifulSoup(self.__response.text, 'lxml')

            setting_value = None

            if setting in ["noteSpeed", "judgeLineTiming"]:
                setting_value = float(soup.select_one('option[selected]').text)
            elif setting == "mask":
                setting_value = int(soup.select_one("div.option_image_select_content.selected > input")["value"])
            elif setting in ["bonusNoteEffect", "mirror"]:
                setting_value = int(soup.select_one('option[selected]')["value"]) == 1
            elif setting == "movie":
                movie_choices = ["ask", False, True]
                setting_value = movie_choices[int(soup.select_one('option[selected]')["value"])]
            else:
                setting_value = int(soup.select_one('option[selected]')["value"])

            game_settings[setting] = setting_value

        #print(game_settings)

        print("* Display...")

        for setting in display_settings:
            self.__response = requests.request("GET", f"{endpoint}/option/{setting}", headers=self.gen_cookie())
            soup = BeautifulSoup(self.__response.text, 'lxml')

            setting_value = None

            if setting in ["informationMask", "guideLineMask", "centerDisplay", "scoreDisplay"]:
                setting_value = int(soup.select_one('option[selected]')["value"])
            elif setting in ["multiRankDisplay", "emblemDisplay", "rateDisplay", "playerLevelDisplay", "gateDirectingSkip", "missionDirectingSkip"]:
                setting_value = int(soup.select_one('option[selected]')["value"]) == 1
            elif setting in ["judgeDetail", "guideMeasureLine"]: 
                setting_value = int(soup.select_one("div.option_image_select_content.selected > input")["value"]) == 1
            else:
                setting_value = int(soup.select_one("div.option_image_select_content.selected > input")["value"])

            display_settings[setting] = setting_value

        #print(display_settings)

        print("* Design...")

        for setting in design_settings:
            self.__response = requests.request("GET", f"{endpoint}/option/{setting}", headers=self.gen_cookie())
            soup = BeautifulSoup(self.__response.text, 'lxml')

            setting_value = None

            if setting == "myColor":
                unlocked_colors = []
                for color in soup.select("div.mycolor-list__set-btn > form > input"):
                    unlocked_colors.append(int(color["value"]))
                setting_value = {"current": get_int(soup.select_one(".current-mycolor__icon > img")["src"]), "unlocked": unlocked_colors}
            elif setting == "touchEffectPop":
                unlocked_effects = []
                for effect in soup.select("div.toucheffect-list__set-btn > form > input"):
                    unlocked_effects.append(int(effect["value"]))
                setting_value = {"current": get_int(soup.select_one(".current-toucheffect__icon > img")["src"]), "unlocked": unlocked_effects}
            elif setting in ["slideColorInvert","touchEffectShoot","keyBeam","rNoteEffect"]:
                setting_value = int(soup.select_one("div.option_image_select_content.selected > input")["value"]) == 1
            else:
                setting_value = int(soup.select_one("div.option_image_select_content.selected > input")["value"])

            design_settings[setting] = setting_value

        #print(design_settings)

        print("* Sound...")

        for setting in sound_settings:
            self.__response = requests.request("GET", f"{endpoint}/option/{setting}", headers=self.gen_cookie())
            soup = BeautifulSoup(self.__response.text, 'lxml')

            setting_value = None

            if setting == "noteTouchSe":
                unlocked_sounds = []
                for sound in soup.select("div.se-list__bottom > form > input"):
                    unlocked_sounds.append(int(sound["value"]))
                setting_value = {"current": get_int(soup.select_one(".current-se__stop-btn > a > audio > source")["src"]), "unlocked": unlocked_sounds}
            elif setting == "charaSound":
                setting_value = int(soup.select_one('option[selected]')["value"]) == 1
            else:
                setting_value = int(soup.select_one('option[selected]').text)

            sound_settings[setting] = setting_value

        #print(sound_settings)


    def scrape(self):
        self.get_user_info()
        self.get_song_data()
        self.get_recent_plays()
        self.get_icons()
        self.get_plates()
        self.get_settings()
        print(time.perf_counter() - self.__start_time)
        f = open(f"dumps/{self.id}.json", "w")
        f.write(jsons.dumps({"player": self}, key_transformer=jsons.KEY_TRANSFORMER_CAMELCASE, strip_privates=True))
        f.close()

    def progress(self):
        return Progress(self.__songs_total, len(self.songs))

    def __init__(self, id):
        self.id = id
        self.__start_time = time.perf_counter()
        self.login_request()
        self.gen_cookie()
        self.__timestamp = time.time()


app = FastAPI()
app.mount("/static/", StaticFiles(directory="frontend", html=True), name="frontend")

users = {}


def scrape_background(user_id):
    users[user_id] = User(int(user_id))
    users[user_id].scrape()

@app.post("/api/scrape")
async def scrape(userId: str = Form(), background_tasks: BackgroundTasks = BackgroundTasks()):
    if not userId.isdigit(): 
        return Response(json={"error":"invalid id"}, status_code=400)
    background_tasks.add_task(scrape_background, userId)

    return RedirectResponse(url="/progress?id=" + userId, status_code=303)

@app.get("/api/getProgress")
async def get_progress(id: str):
    if id in users.keys():
        return users[id].progress()
    else:
        return {"error": "User not found"}

@app.get("/api/getBasicUser")
async def get_basic_user(id: str):
    if id in users.keys():
        user = users[id]
        
        return {
            "name": user.name,
            "level": user.level,
            "title": user.title,
            "points": user.points
        }
    else:
        return {"error": "User not found"}

@app.get("/api/download")
async def download_file(id: str):
    filepath = f"dumps/{id}.json"
    if os.path.exists(filepath):
        return FileResponse(path=filepath, filename=f"{id}.json", media_type='application/octet-stream')
    else:
        return {"error": "File not found"}

@app.get("/book.js")
async def get_bookmarklet():
    with open("book/main.js") as file:
        return Response(content=jsmin(file.read()), media_type="text/javascript")

@app.get("/progress")
async def progress(id: str):
    with open("frontend/index.html") as file:
        return HTMLResponse(file.read(), status_code=200)

@app.get("/")
async def read_index():
    return RedirectResponse(url="/static/index.html")