import asyncio
from Tensura import Tensura
from rich import print
from rich.traceback import install

install()


async def main():
    tmp = Tensura(local=False)
    await tmp.init()
    print(tmp.current_chapter_contents)
    #  print(tmp.chapters)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
