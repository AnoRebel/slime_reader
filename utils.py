from threading import Event, Thread
from time import time
from typing import Dict, List


def get_key(a_dict: Dict[str, str], val: str) -> str:
    """
    Returns a key from a value in a dictionary

    Parameters
    ----------
        a_dict: `Dict[str, str]`
    The dictionary to use
        val: `str`
            The value used to get key from given Dictionary

    Returns
    -------
        key: `str`
            The key from the given value in the Dictionary
    """
    key_list = list(a_dict.keys())
    val_list = list(a_dict.values())
    try:
        position = val_list.index(val)
        return key_list[position]
    except ValueError:
        return "Invalid Chapter!"


def get_index(a_list: List[str], curr: str) -> int:
    """
    Returns the (index + 1) of a value in the given List

    Parameters
    ----------
        a_list: `List[str]`
            The list to use
        curr: `str`
            The value used to get postion in list

    Returns
    -------
        pos: `int`
            The position of value in list + 1
            If not found, 0
    """
    try:
        idx = a_list.index(curr)
        return int(idx) + 1
    except ValueError:
        return 0


def asyncinit(cls):
    """
    Using this function as a decorator allows you to define async `__init__`.
    So you can create objects by `await MyClass(params)`

    NOTE:
    A slight caveat with this is you need to override the `__new__` method

    Example Usage:

    ```py
    @asyncinit
    class Foo(object):
        def __new__(cls):
            # Do nothing. Just to make it work(for me atleast)
            print(cls)
            return super().__new__(cls)

        async def __init__(self, bar):
            self.bar = bar
            print(f"It's ALIVE: {bar}")
    ```
    """

    __new__ = cls.__new__

    async def init(obj, *arg, **kwarg):
        await obj.__init__(*arg, **kwarg)
        return obj

    def new(cls, *arg, **kwarg):
        obj = __new__(cls, *arg, **kwarg)
        return init(obj, *arg, **kwarg)

    cls.__new__ = new
    return cls


class AsyncObject:
    """
    Inheriting this class allows you to define an async `__init__`.
    So you can create objects by doing something like `await MyClass(params)`
    """

    async def __new__(cls, *arg, **kwarg):
        instance = super().__new__(cls)
        await instance.__init__(*arg, **kwarg)
        return instance

    async def __init__(self):
        pass


class setInterval:
    """
    A python version of a setInterval class that allows running functions at an
    interval and cancelling them

    Attributes
    ----------
    interval: `float`
        The time interval in seconds to rerun the given action
    action: `Function`
        An action to be run and rerun after given seconds interval

    Usage
    -----
    `py
    interval = setInterval(seconds, function)
    t = threading.Timer(seconds, inter.cancel)
    t.start()
    `
    """

    def __init__(self, interval, action) -> None:
        self.interval = interval
        self.action = action
        self.stopEvent = Event()
        thread = Thread(target=self.__setInterval)
        thread.start()

    def __setInterval(self) -> None:
        """
        Custom method to run a function every given seconds
        """
        nextTime = time() + self.interval
        while not self.stopEvent.wait(nextTime - time()):
            nextTime += self.interval
            self.action()

    def cancel(self) -> None:
        """
        Stops the current running loop
        """
        self.stopEvent.set()
