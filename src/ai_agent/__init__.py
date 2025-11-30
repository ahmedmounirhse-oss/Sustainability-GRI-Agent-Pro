import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")

if ROOT not in sys.path:
    sys.path.append(ROOT)

if SRC not in sys.path:
    sys.path.append(SRC)

