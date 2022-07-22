import requests, re, time, codecs
from fastapi import FastAPI, Form, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, Response, HTMLResponse
from jsmin import jsmin
from bs4 import BeautifulSoup

# time stuff
from datetime import datetime
import pytz

"""

Left to implement:
- stage up
- settings
- friends
- plates
- navs
- trophies
- total high score (added up all of scores?)
- special song unlocks [/music/unlock]
- favorites
- gates

"""

jst = pytz.timezone("Asia/Tokyo") # used for time conversion
magic = codecs.decode("nvzrVq","rot-13") # hi sega

difficulty_dict = {
    "NORMAL": 0,
    "HARD": 1,
    "EXPERT": 2,
    "INFERNO": 3
}

def get_int(string):
    return int(re.search(r'(\d+)', string).group(1))

class DifficultyStats:
    def __init__(self, score, rate, achieve, play_count):
        self.score = score
        self.rate = rate
        self.achieve = achieve
        self.play_count = play_count

class Progress:
    def __init__(self, bests_total, bests_completed) -> None:
        self.bests_total =  bests_total
        self.bests_completed = bests_completed

class Stage:
    def __init__(self, level, type):
        self.level = level
        self.type = type

class Song:
    def __init__(self, id, name):
        self.id = id
        self.name = name

class PersonalBest(Song):
    play_count = 0
    difficulties = []

class RecentPlay(Song):
    def __init__(self, id, name, timestamp, difficulty, judgements, timings, max_combo):
        self.id = id 
        self.name = name
        self.timestamp = timestamp
        self.difficulty = difficulty
        self.judgements = judgements
        self.timings = timings
        self.max_combo = max_combo

class User:
    name = ""
    wsid = ""
    response = ""
    personal_bests = []
    personal_bests_total = 0
    recents = []
    headers_form_encoded = {"Content-Type": "application/x-www-form-urlencoded"} 
    stage = {}

    def login_request(self):
        print("Logging in with user ID {0}...".format(self.id))
        url = "https://wacca.marv-games.jp/web/login/exec"
        self.response = requests.request("POST", url, data = "{0}={1}".format(magic, self.id), headers=self.headers_form_encoded)
        
    def gen_cookie(self):
        self.wsid = re.search(r'WSID=(\w+);', self.response.headers["Set-Cookie"]).group(1)
        #print("gen_cookie(): new cookie '{0}'".format(self.wsid))
        return {"Cookie": "WSID={0}; WUID={0}".format(self.wsid)}

    def get_user_info(self):
        print("Getting player info...")
        self.response = requests.request("GET", "https://wacca.marv-games.jp/web/player", headers=self.gen_cookie())

        soup = BeautifulSoup(self.response.text, 'html.parser')

        self.name = soup.select_one('.user-info__detail__name').text
        self.title = soup.select_one('.user-info__detail__title').text
        self.level = get_int(soup.select_one('.user-info__detail__lv > span').text)
        self.rate = int(soup.select_one('.rating__data').text)

        stage = soup.select_one('.user-info__icon__stage img')
        if stage:
            tmp = re.search(r'stage_icon_(\d+)_(\d).png', stage["src"])
            self.stage = Stage(tmp.group(1), tmp.group(2))
            print(self.stage.__dict__)

        pointlist = soup.select(".poss-wp")
        self.points = get_int(soup.select_one('.user-info__detail__wp').text)
        self.lifetime_points = get_int(soup.select_one('dl.poss-wp__detail:nth-child(2) > dd:nth-child(1)').text)
        self.used_points = get_int(soup.select_one('dl.poss-wp__detail:nth-child(3) > dd:nth-child(2)').text)
        
        self.ex_tickets = int(soup.select_one('.user-info__detail__ex').text)
        self.icon = get_int(soup.select_one('.icon__image > img')["src"])

    def get_personal_bests(self):
        print("Getting song list...")
        self.response = requests.request("GET", "https://wacca.marv-games.jp/web/music", headers=self.gen_cookie())
        
        soup = BeautifulSoup(self.response.text, 'html.parser')
        
        # Get song data from song list
        songlist = soup.find_all("form",attrs={"name": re.compile("detail")}, limit=5)

        self.personal_bests_total = len(songlist)

        print("Getting song data for {0} songs...".format(self.personal_bests_total))
        for song in songlist:
            self.personal_bests.append(self.scrape_personal_best(PersonalBest(int(song.input["value"]), song.parent.a.div.div.text)))

    def scrape_personal_best(self, song):
        print("* <{0}> [{1}] ".format(song.id, song.name), end='')

        url = "https://wacca.marv-games.jp/web/music/detail"
        self.response = requests.request("POST", url, data = "musicId={0}".format(song.id), headers=self.headers_form_encoded | self.gen_cookie())
        
        soup = BeautifulSoup(self.response.text, 'html.parser')
        song.play_count = get_int(soup.select_one(".song-info__play-count > span").text)
    
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
            song.difficulties.append(diff_stats)
         
        print("({0} diffs)".format(len(diffs))) # mark song as done

    def get_recent_plays(self):
        print("Getting recent plays...")
        self.response = requests.request("GET", "https://wacca.marv-games.jp/web/history", headers=self.gen_cookie())

        soup = BeautifulSoup(self.response.text, 'html.parser')

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
        self.response = requests.request("GET", "https://wacca.marv-games.jp/web/icon", headers=self.gen_cookie())
        soup = BeautifulSoup(self.response.text, 'html.parser')

        self.icons = []
        icon_elements = soup.select(".collection__icon-list .item")
        for icon in icon_elements:
            self.icons.append(int(icon["data-icon_id"]))

    def get_settings(self):
        print("Getting settings...")

        # TODO: actually scrape this

        print("* Game...")
        self.response = requests.request("GET", "https://wacca.marv-games.jp/web/option/gameSetting", headers=self.gen_cookie())
        soup = BeautifulSoup(self.response.text, 'html.parser')

        print("* Display...")
        self.response = requests.request("GET", "https://wacca.marv-games.jp/web/option/displaySetting", headers=self.gen_cookie())
        soup = BeautifulSoup(self.response.text, 'html.parser')

        print("* Design...")
        self.response = requests.request("GET", "https://wacca.marv-games.jp/web/option/designSetting", headers=self.gen_cookie())
        soup = BeautifulSoup(self.response.text, 'html.parser')

        print("* Sound...")
        self.response = requests.request("GET", "https://wacca.marv-games.jp/web/option/soundSetting", headers=self.gen_cookie())
        soup = BeautifulSoup(self.response.text, 'html.parser')


    def scrape(self):
        self.get_user_info()
        #self.get_personal_bests()
        #self.get_recent_plays()
        self.get_icons()
        print(self.__dict__)

    def progress(self):
        return Progress(self.personal_bests_total, len(self.personal_bests))

    def __init__(self, id):
        self.id = id
        self.login_request()
        self.gen_cookie()   
        self.timestamp = time.time()     


app = FastAPI()
app.mount("/static/", StaticFiles(directory="frontend", html=True), name="frontend")

users = {}


def scrape_background(user_id):
    users[user_id] = User(user_id)
    users[user_id].scrape()

@app.post("/api/scrape")
async def scrape(userId: str = Form(), background_tasks: BackgroundTasks = BackgroundTasks()):
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