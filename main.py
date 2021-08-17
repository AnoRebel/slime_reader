import re, os
import pyttsx3
import pygame
import asyncio
import aiohttp
import httpx
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


def asyncinit(cls):
    """
    Using this function as a decorator allows you to define async __init__.
    So you can create objects by `await MyClass(params)`
    NOTE:
    A slight caveat with this is you need to override the __new__ method
    Example usage:
    `py
    @asyncinit
    class Foo(object):
        def __new__(cls):
            # Do nothing. Just to make it work(for me atleast)
            print(cls)
            return super().__new__(cls)

        async def __init__(self, bar):
            self.bar = bar
            print(f"It's ALIVE: {bar}")
    `
    """

    __new__ = cls.__new__

    async def init(obj, *arg, **kwarg):
        await obj.__init__(*arg, **kwarg)
        return obj

    def new(cls, *arg, **kwarg):
        obj = __new__(cls, *arg, **kwarg)
        coro = init(obj, *arg, **kwarg)
        return coro

    cls.__new__ = new
    return cls


class AsyncObject:
    """
    Inheriting this class allows you to define an async __init__.
    So you can create objects by doing something like `await MyClass(params)`
    """

    async def __new__(cls, *arg, **kwarg):
        instance = super().__new__(cls)
        await instance.__init__(*arg, **kwarg)
        return instance

    async def __init__(self):
        pass


class Tensura(AsyncObject):
    """
    Docstring soon
    """

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
        self.current_chapter: str = ""
        self.current_chapter_contents: str = ""
        self.nav_next: str = ""
        self.nav_prev: str = ""
        self.chapter_title: str = ""
        self.chapter_links: List[str] = []
        self.chapter_names: List[str] = []
        self.session: aiohttp.ClientSession = aiohttp.ClientSession(self.HEADERS)
        pygame.mixer.init()
        self.current_chapter_contents = await self.crawl()
        self.error = False

    def __del__(self) -> None:
        pygame.mixer.music.unload()
        pygame.mixer.quit()
        self.session.close()
        if os.path.exists(f"{self.audio_file}.mp3"):
            os.remove(f"{self.audio_file}.mp3")
        if os.path.exists(f"{self.audio_file}.ogg"):
            os.remove(f"{self.audio_file}.ogg")
        self.loop.close()

    async def crawl(self, link=None) -> str:
        """
        Docstring soon
        """
        self.current_chapter = (
            link if link is not None else BASE_URL_ALT if self.alt else BASE_URL
        )
        async with self.session.get(self.current_chapter) as resp:
            if resp.status == 200:
                soup = BeautifulSoup(await resp.text(), "lxml")
                if self.alt:
                    content = await resp.text()
                    # content = resp.text # httpx
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
                    content = await resp.text()
                    # content = resp.text # httpx

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
                        self.chapters[self.chapter_names[i]] = self.chapter_links[i]

                    raw_chapter_contents = soup.find(id="contentall")
                    # Remove unneccessary contents
                    raw_chapter_contents.find(class_="row").decompose()
                    raw_chapter_contents.find("noscript").decompose()
                    chapter_contents = raw_chapter_contents.get_text()
                    return chapter_contents
            else:
                self.error = True
                print(f"{resp.status}: Couldn't load chapter!")
                return f"{resp.status}: Couldn't load chapter!"

    async def load_next(self):
        """
        Docstring soon
        """
        chapter = asyncio.create_task(self.crawl(self.next_chapter))
        # self.current_chapter_contents = await chapter
        return chapter

    async def next(self) -> None:
        """
        Docstring soon
        """
        self.current_chapter_contents = await self.load_next()
        asyncio.create_task(self.read(self.current_chapter_contents))

    async def load_prev(self):
        """
        Docstring soon
        """
        chapter = asyncio.create_task(self.crawl(self.previous_chapter))
        # self.current_chapter_contents = await chapter
        return chapter

    async def prev(self) -> None:
        """
        Docstring soon
        """
        self.current_chapter_contents = await self.load_prev()
        asyncio.create_task(self.read(self.current_chapter_contents))

    async def goto(self, chapter: int) -> None:
        """
        Docstring soon
        """
        if len(self.chapter_links) > 0:
            link = self.chapter_links[chapter + 1]
            chapt = asyncio.create_task(self.crawl(link))
            self.current_chapter_contents = await chapt
        else:
            print(
                f"{self.term.bold}{self.term.red}The site {self.term.green_on_black(self.term.underline(ORIGIN_ALT))} doesn't provide a scrapable chapter list!{self.term.normal}"
            )
            self.read("This site doesn't provide a scrapable chapter list!")

    async def read(self, text: str):
        """
        Docstring soon
        """
        if self.local:
            self.player = pyttsx3.init()
            # I like a female voice
            self.player.setProperty("voice", "english+f3")
            self.player.setProperty("rate", self.rate)
            self.player.say(text)
            task = asyncio.create_task(self.player.runAndWait())
            # await task
        else:
            self.audio_file = uuid4().hex
            tts = gTTS(text=text, lang="en")
            tts.save(f"{self.audio_file}.mp3")
            try:
                import vlc

                self.player = vlc.MediaPlayer(f"{self.audio_file}.mp3")
            except ImportError:
                from pydub import AudioSegment

                AudioSegment.from_mp3(f"{self.audio_file}.mp3").export(
                    f"{self.audio_file}.ogg", format="ogg"
                )
                load = asyncio.create_task(
                    pygame.mixer.music.load(f"{self.audio_file}.ogg")
                )
                self.player = pygame.mixer.music
                await load
            self.play()
            # self.current_chapter_contents = await load_next()
            ## OS players (needs installation)
            # os.system(f"mpg123 {audio.mp3}")
            # os.system(f"mpg321 {audio.mp3}")
            # os.system(f"play -t mp3 {audio.mp3}")

    def progress(self) -> None:
        """
        Docstring soon
        """
        if len(self.chapter_links) > 0:
            print(
                f"{self.term.bold}Reading chapter {self.term.blue_on_black(get_index(self.chapter_links, self.current_chapter))} of {self.term.yellow_on_black(len(self.chapter_links))}, named {self.term.green_on_black(get_key(self.chapters, self.current_chapter))}{self.term.normal}"
            )
            self.read(
                f"Reading chapter {get_index(self.chapter_links, self.current_chapter)} of {len(self.chapter_links)}, named {get_key(self.chapters, self.current_chapter)}"
            )
        else:
            print(
                f"{self.term.bold}Reading {self.term.green_on_black(self.chapter_title)} {self.term.normal}"
            )
            self.read(f"Reading {self.chapter_title}")

    def play(self) -> None:
        """
        Docstring soon
        """
        if self.player is not None:
            self.player.play()

    def pause(self) -> None:
        """
        Docstring soon
        """
        if self.player is not None:
            self.player.pause()

    def unpause(self) -> None:
        """
        Docstring soon
        """
        if self.player is not None:
            try:
                self.player.unpause()
            except (Exception):
                self.player.play()

    def stop(self) -> None:
        """
        Docstring soon
        """
        if self.player is not None:
            self.player.stop()


def get_key(a_dict: Dict[str, str], key: str) -> str:
    """
    Docstring soon
    """
    key_list = list(a_dict.keys())
    val_list = list(a_dict.values())
    try:
        position = val_list.index(key)
        return key_list[position]
    except ValueError:
        return "Invalid Chapter!"


def get_index(a_list: List[str], curr: str) -> int:
    """
    Docstring soon
    """
    try:
        count = a_list.index(curr)
        count = int(count) + 1
        return count
    except ValueError:
        return 0


async def test():
    """
    Docstring soon
    """
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(BASE_URL_ALT) as res:
            content = await res.text()
            soup = BeautifulSoup(content, "lxml")
            chapter_title = soup.find("a", class_="chr-title").get("title", "")
            nav_next_part = soup.find("a", id="next_chap").get("href", "")
            nav_prev_part = soup.find("a", id="prev_chap").get("href", "")
            nav_next = f"{ORIGIN_ALT}{nav_next_part}" if nav_next_part != "" else ""
            nav_prev = f"{ORIGIN_ALT}{nav_prev_part}" if nav_prev_part != "" else ""

            raw_chapter_contents = soup.find("div", id="chr-content")
            chapter_contents = raw_chapter_contents.get_text()
            print(chapter_contents)
            #  return chapter_contents

    async with httpx.AsyncClient(headers=HEADERS) as session:
        res = await session.get(BASE_URL_ALT)
        content = res.text
        soup = BeautifulSoup(content, "lxml")
        chapter_title = soup.find("a", class_="chr-title").get("title", "")
        nav_next_part = soup.find("a", id="next_chap").get("href", "")
        nav_prev_part = soup.find("a", id="prev_chap").get("href", "")
        nav_next = f"{ORIGIN_ALT}{nav_next_part}" if nav_next_part != "" else ""
        nav_prev = f"{ORIGIN_ALT}{nav_prev_part}" if nav_prev_part != "" else ""

        raw_chapter_contents = soup.find("div", id="chr-content")
        chapter_contents = raw_chapter_contents.get_text()
        print(chapter_contents)
        #  return chapter_contents


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())
