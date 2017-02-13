import sys
import os

if __name__ == "__main__":
    _path = os.path.split(__file__)[0]
    if _path:
        os.chdir(_path)
from src import analyse
import src.analyse as analyse
import src.learn as learn

if __name__ == "__main__":
    if len(sys.argv) == 2:
        sentence = sys.argv[1]
        print analyse.get_infos(sentence)
    else:
        msg = "No parameter given!"
        sys.exit(msg)