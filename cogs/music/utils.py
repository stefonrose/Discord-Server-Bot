import re


def categorize(self, query):
    pass


def isURL(self, query):
    regex = (
        "((http|https)://)(www.)?"
        + "[a-zA-Z0-9@:%._\\+~#?&//=]"
        + "{2,256}\\.[a-z]"
        + "{2,6}\\b([-a-zA-Z0-9@:%"
        + "._\\+~#?&//=]*)"
    )

    p = re.compile(regex)

    if re.search(p, query):
        return True
    else:
        return False
