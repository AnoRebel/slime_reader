import re, os
import requests
import pyttsx3
import pygame
import asyncio
import aiohttp
from gtts import gTTS
from uuid import uuid4
from bs4 import BeautifulSoup
from blessings import Terminal
from typing import Dict, List

ORIGIN = "https://novelsonline.net"

ORIGIN_ALT = "https://readnovelfull.com"

HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.115 Safari/537.36"
}

BASE_URL = ORIGIN + "/tensei-shitara-slime-datta-ken-ln/volume-1/chapter-pr"
BASE_URL_ALT = ORIGIN_ALT + "/tensei-shitara-slime-datta-ken/prologue.html"


class Tensura:
    loop = asyncio.get_event_loop()
    term = Terminal()
    HEADERS = {
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.115 Safari/537.36"
    }

    async def __init__(self, local: bool, alt: bool = False, rate: int = 180) -> None:
        self.local: bool = local
        self.alt: bool = alt
        self.rate: int = rate
        self.player = None
        self.chapters: Dict[str, str] = {}
        self.audio_file: str = ""
        self.previous_chapter: int = 0
        self.current_chapter: int = 1
        self.current_chapter_contents: str = ""
        self.next_chapter: int = 2
        self.nav_next: str = ""
        self.nav_prev: str = ""
        self.chapter_title: str = ""
        self.chapter_links: List[str] = []
        self.chapter_names: List[str] = []
        self.session: aiohttp.ClientSession = aiohttp.ClientSession(self.HEADERS)
        pygame.mixer.init()
        self.current_chapter_contents = await self.crawl()

    def __del__(self) -> None:
        pygame.mixer.music.unload()
        pygame.mixer.quit()
        self.session.close()
        if os.path.exists(f"{self.audio_file}.mp3"):
            os.remove(f"{self.audio_file}.mp3")
        if os.path.exists(f"{self.audio_file}.ogg"):
            os.remove(f"{self.audio_file}.ogg")

    async def crawl(self, link=None) -> str:
        link = link if link is not None else BASE_URL_ALT if self.alt else BASE_URL
        async with self.session.get(link) as resp:
            if resp.status == 200:
                soup = BeautifulSoup(await resp.text(), "lxml")
                if self.alt:
                    res = requests.get(BASE_URL_ALT)
                    content = res.text
                    soup = BeautifulSoup(content, "lxml")
                    self.chapter_title = soup.find("a", class_="chr-title").get(
                        "title", ""
                    )
                    nav_next_part = soup.find("a", id="next_chap").get("href", "")
                    nav_prev_part = soup.find("a", id="prev_chap").get("href", "")
                    self.nav_next = (
                        f"{ORIGIN_ALT}{nav_next_part}" if nav_next_part != "" else ""
                    )
                    self.nav_prev = (
                        f"{ORIGIN_ALT}{nav_prev_part}" if nav_prev_part != "" else ""
                    )

                    raw_chapter_contents = soup.find("div", id="chr-content")
                    chapter_contents = raw_chapter_contents.get_text()
                    return chapter_contents
                else:
                    res = requests.get(BASE_URL, headers=HEADERS)
                    content = res.text

                    soup = BeautifulSoup(content, "lxml")
                    self.nav_next = (
                        soup.find("a", class_="next").get("href", "")
                        if soup.find("a", class_="next") is not None
                        else ""
                    )
                    self.nav_prev = (
                        soup.find("a", class_="prev").get("href", "")
                        if soup.find("a", class_="prev") is not None
                        else ""
                    )

                    self.chapter_links = [
                        option.get("value", "")
                        for option in soup.find_all(value=re.compile("chapter"))
                    ]
                    self.chapter_names = [
                        option.get_text()
                        for option in soup.find_all(value=re.compile("chapter"))
                    ]

                    for i in range(len(self.chapter_names)):
                        chapters[self.chapter_names[i]] = self.chapter_links[i]

                    raw_chapter_contents = soup.find(id="contentall")
                    # Remove unneccessary contents
                    raw_chapter_contents.find(class_="row").decompose()
                    raw_chapter_contents.find("noscript").decompose()
                    chapter_contents = raw_chapter_contents.get_text()
                    return chapter_contents
            else:
                return f"{resp.status}: Error reading Novel!"

    async def next(self) -> None:
        # Get link string and update properly to string not int
        chapter = asyncio.create_task(self.crawl(self.next_chapter))
        self.current_chapter_contents = await chapter

    async def prev(self) -> None:
        chapter = asyncio.create_task(self.crawl(self.previous_chapter))
        self.current_chapter_contents = await chapter

    async def goto(self, chapter: int) -> None:
        chapter = asyncio.create_task(self.crawl(""))
        self.current_chapter_contents = await chapter

    async def read(self, text: str):
        if self.local:
            self.player = pyttsx3.init()
            # I like a female voice
            self.player.setProperty("voice", "english+f3")
            self.player.setProperty("rate", self.rate)
            self.player.say(text)
            task = asyncio.create_task(self.player.runAndWait())
            await task
        else:
            self.audio_file = uuid4().hex
            tts = gTTS(text=text, lang="en")
            tts.save(f"{self.audio_file}.mp3")
            # tts.save("audio.mp3")
            try:
                import vlc

                self.player = vlc.MediaPlayer(f"{self.audio_file}.mp3")
                #  self.player = vlc.MediaPlayer("audio.mp3")
            except ImportError:
                from pydub import AudioSegment

                AudioSegment.from_mp3(f"{self.audio_file}.mp3").export(
                    f"{self.audio_file}.ogg", format="ogg"
                )
                load = asyncio.create_task(
                    pygame.mixer.music.load(f"{self.audio_file}.ogg")
                )
                #  AudioSegment.from_mp3("audio.mp3").export("audio.ogg", format="ogg")
                #  load = asyncio.create_task(pygame.mixer.music.load("audio.ogg"))
                await load
                self.player = pygame.mixer.music
            self.play()
            # OS players (needs installation)
            # os.system(f"mpg123 {audio.mp3}")
            # os.system(f"mpg321 {audio.mp3}")
            # os.system(f"play -t mp3 {audio.mp3}")

    def progress(self):
        pass

    def update_chapters(self, kind):
        if type(kind) == int:
            self.previous_chapter = self.current_chapter
            self.current_chapter = kind
        else:
            if kind == "prev":
                if self.previous_chapter == 0:
                    self.current_chapter = 1
                else:
                    self.previous_chapter = self.current_chapter
                    self.current_chapter = self.current_chapter - 1
            elif kind == "next":
                self.previous_chapter = self.current_chapter
                self.current_chapter = self.current_chapter + 1
        self.next_chapter = self.current_chapter + 1

    def play(self) -> None:
        if self.player is not None:
            self.player.play()

    def pause(self) -> None:
        if self.player is not None:
            self.player.pause()

    def unpause(self) -> None:
        if self.player is not None:
            try:
                self.player.unpause()
            except (Exception):
                self.player.play()

    def stop(self):
        if self.player is not None:
            self.player.stop()

    def pprint(self, data):
        print(f"{self.term} {data}")


chapters = {}


def main():
    import cProfile, pstats

    with cProfile.Profile() as pr:
        res = requests.get(BASE_URL, headers=HEADERS)
        content = res.text

        soup = BeautifulSoup(content, "lxml")
        nav_next = (
            soup.find("a", class_="next").get("href", "")
            if soup.find("a", class_="next") is not None
            else ""
        )
        nav_prev = (
            soup.find("a", class_="prev").get("href", "")
            if soup.find("a", class_="prev") is not None
            else ""
        )

        chapter_link = [
            option.get("value", "")
            for option in soup.find_all(value=re.compile("chapter"))
        ]
        chapter_name = [
            option.get_text() for option in soup.find_all(value=re.compile("chapter"))
        ]

        for i in range(len(chapter_name)):
            chapters[chapter_name[i]] = chapter_link[i]

        raw_chapter_contents = soup.find(id="contentall")
        # Remove unneccessary contents
        raw_chapter_contents.find(class_="row").decompose()
        raw_chapter_contents.find("noscript").decompose()
        chapter_contents = raw_chapter_contents.get_text()
        print(nav_next)
        print(nav_prev)
        # return chapter_contents
    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    #  stats.print_stats()
    stats.dump_stats(filename="profiled.prof")


def main_alt():
    import cProfile, pstats

    with cProfile.Profile() as pr:
        res = requests.get(BASE_URL_ALT)
        content = res.text
        soup = BeautifulSoup(content, "lxml")
        chapter_title = soup.find("a", class_="chr-title").get("title", "")
        nav_next_part = soup.find("a", id="next_chap").get("href", "")
        nav_prev_part = soup.find("a", id="prev_chap").get("href", "")
        nav_next = f"{ORIGIN_ALT}{nav_next_part}" if nav_next_part != "" else ""
        nav_prev = f"{ORIGIN_ALT}{nav_prev_part}" if nav_prev_part != "" else ""

        raw_chapter_contents = soup.find("div", id="chr-content")
        chapter_contents = raw_chapter_contents.get_text()
        #  return chapter_contents
    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    #  stats.print_stats()
    stats.dump_stats(filename="profiled_alt.prof")


if __name__ == "__main__":
    from cProfile import Profile
    from pstats import Stats, SortKey

    with Profile() as pr:
        main()
        main_alt()
    stats = Stats(pr)
    stats.sort_stats(SortKey.TIME)
    #  stats.print_stats()
    stats.dump_stats(filename="profiled_all.prof")
