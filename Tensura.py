import asyncio
import os
import re
from typing import Dict, List, Optional
from uuid import uuid4

import aiohttp
import httpx
import pygame
import pyttsx3
from blessings import Terminal
from bs4 import BeautifulSoup
from gtts import gTTS
from rich import print
from rich.traceback import install

from utils import AsyncObject, get_index, get_key

install()


class Tensura:
    """
    Tensura class, inheriting the AsyncObject class to enable async `__init__`
    This class loads a link(depending on passed param), crawls it
    And optionally reads to you either online or offline

    Attributes
    ----------
    local: `bool`
        either use local reader(pyttsx3 or VLC) or online(gTTS) reader
    alt: `bool` (Default: False)
        Use https://readnovelfull.com if true, else https://novelsonline.net

    Methods
    -------
    `async crawl(link=None)`:
        Crawls the provided link, fills some global variable and returns the
        content
    `async read(text: str)`:
        Reads the given text using either gTTS or local
    `async load_next()`:
        Load the next chapter but don't read it
    `async next()`:
        Set the next chapter and read(optional)
    `async load_prev()`:
        Load the previous chapter but don't read it
    `async prev()`:
        Set the previous chapter and read(optional)
    `async goto(chapter: int)`:
        Go to the given chapter number for the site that supports it
    `progress()`:
        Returns the current progress of your reading
    `play()`:
        Using the configured player, play the current chapter
    `pause()`:
        Using the configured player, pause the reading
    `unpause()`:
        Using the configured player, play the paused reading
    `stop()`:
        Using the configured player, stop playing
    """

    loop = asyncio.get_event_loop()
    term = Terminal()
    ORIGIN = "https://novelsonline.net"
    ORIGIN_ALT = "https://readnovelfull.com"
    BASE_URL = ORIGIN + "/tensei-shitara-slime-datta-ken-ln/volume-1/chapter-pr"
    BASE_URL_ALT = ORIGIN_ALT + "/tensei-shitara-slime-datta-ken/prologue.html"
    HEADERS = {
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"
    }

    def __init__(self, local: bool, alt: bool = False) -> None:
        self.local: bool = local
        self.alt: bool = alt
        self.player = None
        self.is_playing: bool = False
        self.chapters: Dict[str, str] = {}
        self.audio_file: str = ""
        self.current_chapter: str = ""
        self.current_chapter_contents: str = ""
        self.nav_next: str = ""
        self.nav_prev: str = ""
        self.chapter_title: str = ""
        self.chapter_links: List[str] = []
        self.chapter_names: List[str] = []
        pygame.mixer.init()
        self.error = False

    def __del__(self) -> None:
        pygame.mixer.music.unload()
        pygame.mixer.quit()
        closed = self.session.close()
        if os.path.exists(f"{self.audio_file}.mp3"):
            os.remove(f"{self.audio_file}.mp3")
        if os.path.exists(f"{self.audio_file}.ogg"):
            os.remove(f"{self.audio_file}.ogg")
        self.loop.close()

    async def init(self):
        self.session: aiohttp.ClientSession = aiohttp.ClientSession(
            headers=self.HEADERS
        )
        self.current_chapter_contents = await self.crawl()

    async def crawl(self, link=None) -> str:
        """
        Crawls the provided link or the default link(first chapter)

        Parameters
        ----------
        link : `str, optional`
            The link to the current chapter to be read
            If `None`, loads the first chapter (default is `None`)

        Returns
        -------
        chapter_content: `str`
            The crawled chapter contents
        """
        self.current_chapter = (
            link
            if link is not None
            else self.BASE_URL_ALT
            if self.alt
            else self.BASE_URL
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
                        f"{self.ORIGIN_ALT}{nav_next_part}"
                        if nav_next_part != ""
                        else ""
                    )
                    self.nav_prev = (
                        f"{self.ORIGIN_ALT}{nav_prev_part}"
                        if nav_prev_part != ""
                        else ""
                    )

                    raw_chapter_contents = soup.find("div", id="chr-content")
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
                    # Remove unnecessary contents
                    try:
                        raw_chapter_contents.find(class_="row").decompose()
                    except AttributeError:
                        pass
                    try:
                        raw_chapter_contents.find("noscript").decompose()
                    except AttributeError:
                        pass
                return raw_chapter_contents.get_text()
            else:
                self.error = True
                print(f"{resp.status}: Couldn't load chapter!")
                return f"{resp.status}: Couldn't load chapter!"

    async def read(self, text: str) -> None:
        """
        Reads the provided text.

        Parameters
        ----------
        text : `str`
            Text to be read aloud

        Returns
        -------
        `None`
        """
        if self.local:
            self.player = pyttsx3.init()
            # I like a female voice
            self.player.setProperty("voice", "english+f3")
            self.player.setProperty("rate", 180)
            self.player.say(text)
            task = asyncio.create_task(self.player.runAndWait())
            # await task
            self.is_playing = True
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

    async def load_next(self) -> asyncio.Task:
        """
        Crawls the next chapter but does not read it.
        Await `self.next()` to read it.

        Returns
        -------
        Task: `Future`
            The task to be awaited
        """
        chapter = asyncio.create_task(self.crawl(self.nav_next))
        self.current_chapter_contents = await chapter
        return chapter

    async def next(self) -> None:
        """
        Set the next chapter as the current chapter and read it(optional).

        Returns
        -------
        `None`
        """
        self.current_chapter_contents = await self.load_next()
        asyncio.create_task(self.read(self.current_chapter_contents))

    async def load_prev(self) -> asyncio.Task:
        """
        Crawls the previous chapter but does not read it.
        Await `self.prev()` to read it

        Returns
        -------
        Task: `Future`
            The task to be awaited
        """
        chapter = asyncio.create_task(self.crawl(self.nav_prev))
        self.current_chapter_contents = await chapter
        return chapter

    async def prev(self) -> None:
        """
        Set the previous chapter as the current chapter and read it(optional).

        Returns
        -------
        `None`
        """
        self.current_chapter_contents = await self.load_prev()
        asyncio.create_task(self.read(self.current_chapter_contents))

    async def goto(self, chapter: int) -> None:
        """
        If available and if site provides chapters, crawl it and set as current chapter.

        Parameters
        ----------
        chapter : `int`
            The chapter to crawl for reading

        Returns
        -------
        `None`
        """
        if len(self.chapter_links) > 0:
            link = self.chapter_links[chapter - 1]
            chapt = asyncio.create_task(self.crawl(link))
            self.current_chapter_contents = await chapt
        else:
            print(
                f"{self.term.bold}{self.term.red}The site {self.term.green_on_black(self.term.underline(self.ORIGIN_ALT))} doesn't provide a scrapable chapter list!{self.term.normal}"
            )
            self.read("This site doesn't provide a scrapable chapter list!")

    def progress(self) -> Optional[str]:
        """
        Prints out and reads aloud the current progress/chapter being read.

        Returns
        -------
        `String or None`
        """
        if len(self.chapter_links) > 0:
            print(
                f"{self.term.bold}Reading chapter {self.term.blue_on_black(get_index(self.chapter_links, self.current_chapter))} of {self.term.yellow_on_black(len(self.chapter_links))}, named {self.term.green_on_black(get_key(self.chapters, self.current_chapter))}{self.term.normal}"
            )
            self.read(
                f"Reading chapter {get_index(self.chapter_links, self.current_chapter)} of {len(self.chapter_links)}, named {get_key(self.chapters, self.current_chapter)}"
            )
            return f"Reading chapter {get_index(self.chapter_links, self.current_chapter)} of {len(self.chapter_links)}, named {get_key(self.chapters, self.current_chapter)}"
        else:
            print(
                f"{self.term.bold}Reading {self.term.green_on_black(self.chapter_title)} {self.term.normal}"
            )
            self.read(f"Reading {self.chapter_title}")
            return f"Reading {self.chapter_title}"

    def play(self) -> None:
        """
        Plays the currently loaded chapter, with the configured player.

        Returns
        -------
        `None`
        """
        if self.player is not None:
            self.player.play()
            self.is_playing = True

    def pause(self) -> None:
        """
        Pauses the currently playing chapter, if any.

        Returns
        -------
        `None`
        """
        if self.player is not None:
            self.player.pause()
            self.is_playing = False

    def unpause(self) -> None:
        """
        Unpauses/plays the currently paused chapter.

        Returns
        -------
        `None`
        """
        if self.player is not None:
            try:
                self.player.unpause()
                self.is_playing = True
            except (Exception):
                self.player.play()

    def stop(self) -> None:
        """
        Stops the currently playing chapter, if any.

        Returns
        -------
        `None`
        """
        if self.player is not None:
            self.player.stop()


async def test(local: bool = True) -> None:
    """
    A simple test method for `aiohttp` and `httpx`

    Parameters
    ----------
    local: `bool`
        Whether to use offline(local) reader or online reader (default: `True`)

    Returns
    -------
    `None`
    """
    ORIGIN = "https://novelsonline.net"
    ORIGIN_ALT = "https://readnovelfull.com"
    BASE_URL = ORIGIN + "/tensei-shitara-slime-datta-ken-ln/volume-1/chapter-pr"
    BASE_URL_ALT = ORIGIN_ALT + "/tensei-shitara-slime-datta-ken/prologue.html"
    HEADERS = {
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"
    }
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(BASE_URL) as res:
            content = await res.text()
            print(content)
            soup = BeautifulSoup(content, "lxml")
            chapter_title = soup.find("a", class_="chr-title").get("title", "")
            nav_next_part = soup.find("a", id="next_chap").get("href", "")
            nav_prev_part = soup.find("a", id="prev_chap").get("href", "")
            nav_next = f"{ORIGIN_ALT}{nav_next_part}" if nav_next_part != "" else ""
            nav_prev = f"{ORIGIN_ALT}{nav_prev_part}" if nav_prev_part != "" else ""

            raw_chapter_contents = soup.find("div", id="chr-content")
            chapter_contents = raw_chapter_contents.get_text()
            print(chapter_contents)
            if local:
                player = pyttsx3.init()
                # I like a female voice
                player.setProperty("voice", "english+f3")
                player.setProperty("rate", 180)
                player.say(chapter_contents)
                task = asyncio.create_task(player.runAndWait())
                # await task
            else:
                audio_file = uuid4().hex
                if os.path.exists(f"{audio_file}.mp3"):
                    os.remove(f"{audio_file}.mp3")
                if os.path.exists(f"{audio_file}.ogg"):
                    os.remove(f"{audio_file}.ogg")
                tts = gTTS(text=chapter_contents, lang="en")
                tts.save(f"{audio_file}.mp3")
                try:
                    import vlc

                    player = vlc.MediaPlayer(f"{audio_file}.mp3")
                except ImportError:
                    from pydub import AudioSegment

                    pygame.mixer.init()

                    AudioSegment.from_mp3(f"{audio_file}.mp3").export(
                        f"{audio_file}.ogg", format="ogg"
                    )
                    load = asyncio.create_task(
                        pygame.mixer.music.load(f"{audio_file}.ogg")
                    )
                    player = pygame.mixer.music
                    await load
                # player.play()
                ## OS players (needs installation)
                # os.system(f"mpg123 {audio.mp3}")
                # os.system(f"mpg321 {audio.mp3}")
                # os.system(f"play -t mp3 {audio.mp3}")
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
        if local:
            player = pyttsx3.init()
            # I like a female voice
            player.setProperty("voice", "english+f3")
            player.setProperty("rate", 180)
            player.say(chapter_contents)
            task = asyncio.create_task(player.runAndWait())
            # await task
        else:
            audio_file = uuid4().hex
            if os.path.exists(f"{audio_file}.mp3"):
                os.remove(f"{audio_file}.mp3")
            if os.path.exists(f"{audio_file}.ogg"):
                os.remove(f"{audio_file}.ogg")
            tts = gTTS(text=chapter_contents, lang="en")
            tts.save(f"{audio_file}.mp3")
            try:
                import vlc

                player = vlc.MediaPlayer(f"{audio_file}.mp3")
            except ImportError:
                from pydub import AudioSegment

                pygame.mixer.init()

                AudioSegment.from_mp3(f"{audio_file}.mp3").export(
                    f"{audio_file}.ogg", format="ogg"
                )
                load = asyncio.create_task(pygame.mixer.music.load(f"{audio_file}.ogg"))
                player = pygame.mixer.music
                await load
            # player.play()
            ## OS players (needs installation)
            # os.system(f"mpg123 {audio.mp3}")
            # os.system(f"mpg321 {audio.mp3}")
            # os.system(f"play -t mp3 {audio.mp3}")
        #  return chapter_contents


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())
