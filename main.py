import os, requests, re, time, codecs, json, jsons
from fastapi import FastAPI, Form, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, Response, HTMLResponse, FileResponse
from jsmin import jsmin
from bs4 import BeautifulSoup
from user_agent import generate_user_agent

# validation
from jsonschema import validate

# time stuff
from datetime import datetime
import pytz

"""

Left to implement:
- stage up
- friends
- titles
- trophies
- bingo

"""

endpoint = os.environ.get("MYPAGE_ENDPOINT")
endpoint = endpoint if endpoint is not None else ""

jst = pytz.timezone("Asia/Tokyo") # used for time conversion
magic = codecs.decode("nvzrVq","rot-13") # hi sega
full_dump = False # dump play count

difficulty_dict = {
    "NORMAL": 0,
    "HARD": 1,
    "EXPERT": 2,
    "INFERNO": 3
}

box_item_types = {
    "マイカラー": "myColor",
    "ノーツタッチSE": "noteTouchSe",
    "アイコン": "icon",
    "称号": "title",
    "プレート": "plate"
}

def get_int(string):
    if any(char.isdigit() for char in string):
        return int(re.search(r'(\d+)', string).group(1))
    else:
        raise TypeError(f"Integer not found in \"{string}\"")

class DifficultyStats:
    def __init__(self, score, rating, achieve, play_count, leaderboard):
        self.score = score
        self.rating = rating
        self.achieve = achieve
        self.play_count = play_count
        self.leaderboard = leaderboard

class BasicDifficultyStats:
    def __init__(self, score, rating, achieve):
        self.score = score
        self.rating = rating
        self.achieve = achieve

class Progress:
    def __init__(self, songs_total, songs_completed) -> None:
        self.songs_total =  songs_total
        self.songs_completed = songs_completed

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

class Box:
    def __init__(self, id):
        self.id = id
        self.items = []

class BoxItem:
    def __init__(self, name, type, amount, unlocked):
        self.name = name
        self.type = type
        self.amount = amount
        self.unlocked = unlocked

class Gate:
    def __init__(self, id, level, points, points_max):
        self.id = id
        self.level = level
        self.points = points
        self.points_max = points_max

class Settings: 
    def __init__(self, game, display, design, sound):
        self.game = game
        self.display = display
        self.design = design
        self.sound = sound

class GameSettings:
    noteSpeed = None
    judgeLineTiming = None
    mask = None
    movie = None
    bonusNoteEffect = None
    mirror = None
    giveup = None

class DisplaySettings:
    judgePosition = None
    judgeDetail = None
    informationMask = None 
    guideLineInterval = None 
    guideLineMask = None 
    guideMeasureLine = None 
    centerDisplay = None
    scoreDisplay = None
    multiRankDisplay = None
    emblemDisplay = None
    rateDisplay = None
    playerLevelDisplay = None
    gateDirectingSkip = None
    missionDirectingSkip = None

class DesignSettings:
    myColor = { "current": None, "unlocked": [] }
    noteWidth = None
    touchNoteColor = None
    chainNoteColor = None
    slideNoteLeftColor = None
    slideNoteRightColor = None
    snapNoteUpColor = None
    snapNoteDownColor = None
    holdNoteColor = None
    slideColorInvert = None
    touchEffectPop = None
    touchEffectShoot = None
    keyBeam = None
    rNoteEffect = None

class SoundSettings:
    noteTouchSe = None
    bgmVolume = None
    guideSoundVolume = None
    touchNoteVolume = None
    holdNoteVolume = None
    slideNoteVolume = None
    snapNoteVolume = None
    chainNoteVolume = None
    bonusNoteVolume = None
    charaSound = None
    rNoteVolume = None

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
        self.__response = requests.request("POST", f"{endpoint}/login/exec", data=f"{magic}={self.id}", headers=self.__headers_form_encoded | {"User-Agent": self.__ua})
        
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

        self.total_high_scores = [0, 0, 0, 0]

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
                    if diff == "inferno" and song.select_one(".diff_icon_inferno").text == "INFERNO 0":
                        continue
                    score = get_int(song.select_one(f".song-info__bottom-wrap.difficulty__{diff} .playdata__score-list__song-info__score").text)
                    self.total_high_scores[diffs.index(diff)] += score

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
            print(self.total_high_scores)

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
            self.total_high_scores[diffs.index(diff)] += score
            
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

            self.__response = requests.request("POST", f"{endpoint}/ranking/musicHighScore/detail", data = f"musicId={song.id}&rankCategory={diffs.index(diff)+1}", headers=self.__headers_form_encoded | self.gen_cookie())
            soup = BeautifulSoup(self.__response.text, 'lxml')

            temp_lb = soup.select_one(".ranking__score__rank.top-rank").text.strip()

            lb_img = soup.select_one(".ranking__score__rank.top-rank > img")
            if lb_img is not None and "ranking/icon-" in lb_img["src"]:
                leaderboard = get_int(soup.select_one(".ranking__score__rank.top-rank > img")["src"])
            else:
                leaderboard = get_int(temp_lb) if temp_lb != "-位" else 0

            diff_stats = DifficultyStats(score, rate, achieve, play_count, leaderboard)
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
            song_id = int(song.select_one("#musicId")["value"])

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

    def get_navigators(self):
        print("Getting unlocked navigators...")
        self.__response = requests.request("GET", f"{endpoint}/naviCharacter", headers=self.gen_cookie())
        soup = BeautifulSoup(self.__response.text, 'lxml')

        self.navigator = get_int(soup.select_one(".current-navi-character__icon").img["src"])

        self.navigators = []
        navi_elements = soup.select(".collection__navi-character-list #naviCharacterId")
        for navi in navi_elements:
            self.navigators.append(int(navi["value"]))

    def get_boxes(self):
        print("Getting box stats...")
        self.__response = requests.request("GET", f"{endpoint}/box", headers=self.gen_cookie())
        soup = BeautifulSoup(self.__response.text, 'lxml')

        boxes = soup.select(".box__banner #boxId")

        self.boxes = []

        for box in boxes:
            self.boxes.append(self.scrape_box(int(box["value"])))

    def scrape_box(self,box):
        #print(f"* Scraping box {box}...")
        self.__response = requests.request("POST", f"{endpoint}/box/detail", data=f"boxId={box}", headers=self.gen_cookie() | self.__headers_form_encoded)
        soup = BeautifulSoup(self.__response.text, 'lxml')

        items = soup.select(".box__box-list .box-list__title-list li")

        box_item = Box(box)

        #print(f"{len(items)} items")
        for item in items:
            item_name = item.p.text
            item_type = box_item_types[item.select_one(".title-list__bottom .title-list__title").text.strip()]
            item_meta = item.select_one(".title-list__bottom .title-list__num").text.strip()
            item_amount = get_int(item_meta) if item_meta != "未獲得" else 0 
            item_unlocked = item.get("class") != ["unacquired"]

            box_item.items.append(BoxItem(item_name, item_type, item_amount, item_unlocked))
            #print(f"- {item_name} ({item_type}) [{item_amount}] <{item_unlocked}>")
        return box_item

    def get_unlocks(self):
        print("Getting unlocked special songs...")
        self.__response = requests.request("GET", f"{endpoint}/music/unlock", headers=self.gen_cookie())
        soup = BeautifulSoup(self.__response.text, 'lxml')

        self.unlocks = []
        icon_elements = soup.select(".song-open__song-list .song-list__list-wrap .item-content:not(.is-lock) .song-list__song-icon img")
        for icon in icon_elements:
            self.unlocks.append(get_int(icon["src"]))

    def get_gates(self):
        print("Getting gate infomation...")
        self.__response = requests.request("GET", f"{endpoint}/gate", headers=self.gen_cookie())
        soup = BeautifulSoup(self.__response.text, 'lxml')

        gates = soup.select(".gate__list__wrap #gate_id")

        self.gates = []
        for gate in gates:
            self.gates.append(self.scrape_gate(int(gate["value"])))


    def scrape_gate(self, gate):
        print(f"* Scraping gate {gate}")
        self.__response = requests.request("POST", f"{endpoint}/gate/detail", data=f"gate_id={gate}", headers=self.gen_cookie() | self.__headers_form_encoded)
        soup = BeautifulSoup(self.__response.text, 'lxml')

        gate_level = get_int(soup.select_one(".progress-circle").text)
        gate_progress = list(map(int, soup.select_one(".progress-count").text.split("/")))

        items = soup.select(".open-icons li img")
        
        return Gate(gate, gate_level, gate_progress[0], gate_progress[1])
        

    def get_settings(self):
        print("Getting settings...")

        self.settings = Settings(GameSettings(), DisplaySettings(), DesignSettings(), SoundSettings())

        print("* Game...")

        for setting in ["noteSpeed","judgeLineTiming","mask","movie","bonusNoteEffect","mirror","giveup"]:
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

            setattr(self.settings.game, setting, setting_value)

        print("* Display...")

        for setting in ["judgePosition","judgeDetail","informationMask","guideLineInterval","guideLineMask","guideMeasureLine","centerDisplay","scoreDisplay","multiRankDisplay","emblemDisplay","rateDisplay","playerLevelDisplay","gateDirectingSkip","missionDirectingSkip"]:
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

            setattr(self.settings.display, setting, setting_value)

        print("* Design...")

        for setting in ["myColor","noteWidth","touchNoteColor","chainNoteColor","slideNoteLeftColor","slideNoteRightColor","snapNoteUpColor","snapNoteDownColor","holdNoteColor","slideColorInvert","touchEffectPop","touchEffectShoot","keyBeam","rNoteEffect"]:
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

            setattr(self.settings.design, setting, setting_value)

        print("* Sound...")

        for setting in ["noteTouchSe","bgmVolume","guideSoundVolume","touchNoteVolume","holdNoteVolume","slideNoteVolume","snapNoteVolume","chainNoteVolume","bonusNoteVolume","charaSound","rNoteVolume"]:
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

            setattr(self.settings.sound, setting, setting_value)

    def scrape(self):
        self.get_user_info()
        self.get_song_data()
        self.get_recent_plays()
        self.get_icons()
        self.get_plates()
        self.get_navigators()
        self.get_boxes()
        self.get_gates()
        self.get_unlocks()
        self.get_settings()
        print(time.perf_counter() - self.__start_time)
        user_json = jsons.dumps({"player": self}, key_transformer=jsons.KEY_TRANSFORMER_CAMELCASE, strip_privates=True)
        validate(instance=jsons.loads(user_json), schema=json.loads(open("schema/wacca_data.schema.json", "r").read()))
        f = open(f"dumps/{self.id}.json", "w")
        f.write(user_json)
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
        return Response(content=jsmin(file.read()), media_type="text/javascript", headers={"Access-Control-Allow-Origin": "*"})

@app.get("/progress")
async def progress(id: str):
    with open("frontend/index.html") as file:
        return HTMLResponse(file.read(), status_code=200)

@app.get("/")
async def read_index():
    return RedirectResponse(url="/static/index.html")