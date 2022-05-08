import re


def sanitize(title: str):
    first_scrub = re.sub("[\(\[](.*?)[\)\]]", "", title).strip()
    second_scrub = re.sub(" {2,}", " ", first_scrub)
    return second_scrub


def isURL(query):
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
