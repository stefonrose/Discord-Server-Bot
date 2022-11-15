import validators, re, random, os
from urllib.parse import parse_qs, urlparse


img = {
    "kid-mack": True,
    "mack1": True,
    "mack2": True,
    "mack3": True,
    "mack4": True,
    "mack5": True,
    "mack6": True,
    "mack7": True,
    "mack8": False,
}
images = os.listdir("cogs/random/mag")
names = [os.path.splitext(image)[0] for image in images]
name = random.choice(names)
image = next(i for i in images if name in i)
print(image)
