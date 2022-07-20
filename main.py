from audioop import ratecv
from multiprocessing import get_start_method
import requests, re
from fastapi import FastAPI, Form
from bs4 import BeautifulSoup

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
    
class SongData:
    total_palays
    difficulties = []

class Song:
    def scrape(self):
        
        
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.data = self.scrape()


class User:
    wsid = ""
    response = ""
    songs = []
    headers_form_encoded = {"Content-Type": "application/x-www-form-urlencoded"} 

    def login_request(self):
        url = "https://wacca.marv-games.jp/web/login/exec"
        self.response = requests.request("POST", url, data = "aimeId=" + str(self.id), headers=self.headers_form_encoded)
        
    
    def update_wsid(self):
        self.wsid = re.search(r'WSID=(\w+);', self.response.headers["Set-Cookie"]).group(1)
    
    def gen_cookie(self):
        return "WSID="+self.wsid+"; WUID="+self.wsid

    def get_songs(self):
        response = requests.request("GET", "https://wacca.marv-games.jp/web/music", headers = { "Cookie": self.gen_cookie() })
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get  
        for i in soup.find_all("form",attrs={"name": re.compile("detail")}):
            song = Song(int(i.input["value"]), i.parent.a.div.div.string)
            self.songs.append(song)

    def __init__(self, id):
        self.id = id
        self.login_request()
        self.update_wsid()
        self.get_songs()


app = FastAPI()

@app.post("/")
async def root(aimeId: str = Form()):
    user = User(aimeId)
    return "Success"