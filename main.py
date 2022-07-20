from audioop import ratecv
from multiprocessing import get_start_method
from git import Diff
from numpy import diff
import requests, re
from fastapi import FastAPI, Form
from bs4 import BeautifulSoup

def get_int(string):
    return int(re.search(r'(\d+)', string).group(1))

class DifficultyStats:
    def __init__(self, score, rate, achieve, play_count):
        self.score = score
        self.rate = rate
        self.achieve = achieve
        self.play_count = play_count
    
    # pink one: total_plays
    # play count: black text about pink oval
    # score: black text next to circle and triangle
    # rate = circle icon (0-13) or none
    # achieve = triangle (0-3)
    #https://wacca.marv-games.jp/web/music/detail 
    
class Song:
    total_plays = 0
    difficulties = []

    def __init__(self, id, name):
        self.id = id
        self.name = name


class User:
    wsid = ""
    response = ""
    songs = []
    headers_form_encoded = {"Content-Type": "application/x-www-form-urlencoded"} 

    def login_request(self):
        url = "https://wacca.marv-games.jp/web/login/exec"
        self.response = requests.request("POST", url, data = "aimeId=" + str(self.id), headers=self.headers_form_encoded)
        
    def gen_cookie(self):
        self.wsid = re.search(r'WSID=(\w+);', self.response.headers["Set-Cookie"]).group(1)
        return "WSID="+self.wsid+"; WUID="+self.wsid

    def scrape_song(self, song):
        url = "https://wacca.marv-games.jp/web/music/detail"
        self.response = requests.request("POST", url, data = "musicId=" + str(song.id), headers={"Content-Type": "application/x-www-form-urlencoded", "Cookie": self.gen_cookie() })
        soup = BeautifulSoup(self.response.text, 'html.parser')
        
        
        song.total_plays = get_int(soup.select_one(".song-info__play-count > span").text)
    

        # Selector for difficulties
        diffs = soup.select(".score-detail__list__song-info")

        song.difficulties = []


        for diff in diffs:
            play_count = get_int(diff.select_one(".song-info__top__play-count").text)
            score = get_int(diff.select_one(".song-info__score").text)
            
            # difficulty name
            # print(diff.select_one(".song-info__top__lv > div").text)
            
            # difficulty rate and achieve
            icons = diff.select(".score-detail__icon > div > img")
            rate = icons[0]["src"].replace("/img/web/music/rate_icon/", "").split(".")[0]
            achieve = icons[1]["src"].replace("/img/web/music/achieve_icon/", "").split(".")[0]

            diff_stats = DifficultyStats(score, rate, achieve, play_count)
            song.difficulties.append(diff_stats)
            
        print(song.__dict__)

        for diff in song.difficulties:
            print(diff.__dict__)

    def get_songs(self):
        self.response = requests.request("GET", "https://wacca.marv-games.jp/web/music", headers = { "Cookie": self.gen_cookie() })
        
        soup = BeautifulSoup(self.response.text, 'html.parser')
        
        # Get  
        for i in soup.find_all("form",attrs={"name": re.compile("detail")}):
            song = Song(int(i.input["value"]), i.parent.a.div.div.string)
            self.songs.append(self.scrape_song(song))

    def __init__(self, id):
        self.id = id
        self.login_request()
        self.gen_cookie()
        self.get_songs()


app = FastAPI()

@app.post("/")
async def root(aimeId: str = Form()):
    user = User(aimeId)
    return "Success"