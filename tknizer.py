#tokenizer borrows from nltk, emojipy, jie_ba_tokenizer, and TinySegmenter
#much borrowed from https://github.com/erikavaris/tokenizer/blob/master/tokenizer/tokenizer.py
import nltk
from nltk.tokenize.casual import remove_handles, reduce_lengthening, _str_to_unicode, _replace_html_entities # EMOTICONS, EMOTICON_RE
import emojipy
from  emojipy.ruleset import unicode_replace
import re
from .reg import Regularizer
import unicodedata
import pkg_resources
import regex
import itertools
import collections
import tinysegmenter
import html
import re
import emojipy
from  emojipy.ruleset import unicode_replace

ascii = False
unicode_alt = True
sprites = False
image_png_path = 'https://cdn.jsdelivr.net/emojione/assets/3.1/png/64/'
ignored_regexp = '<object[^>]*>.*?<\/object>|<span[^>]*>.*?<\/span>|<(?:object|embed|svg|img|div|span|p|a)[^>]*>'
unicode_regexp = "(" + '|'.join([re.escape(x.decode("utf-8")) for x in sorted(unicode_replace.keys(), key=len, reverse=True)]) + ")"
shortcode_regexp = ':([-+\\w]+):'
ascii_regexp = '(\\<3|&lt;3|\\<\\/3|&lt;\\/3|\\:\'\\)|\\:\'\\-\\)|\\:D|\\:\\-D|\\=D|\\:\\)|\\:\\-\\)|\\=\\]|\\=\\)|\\:\\]|\'\\:\\)|\'\\:\\-\\)|\'\\=\\)|\'\\:D|\'\\:\\-D|\'\\=D|\\>\\:\\)|&gt;\\:\\)|\\>;\\)|&gt;;\\)|\\>\\:\\-\\)|&gt;\\:\\-\\)|\\>\\=\\)|&gt;\\=\\)|;\\)|;\\-\\)|\\*\\-\\)|\\*\\)|;\\-\\]|;\\]|;D|;\\^\\)|\'\\:\\(|\'\\:\\-\\(|\'\\=\\(|\\:\\*|\\:\\-\\*|\\=\\*|\\:\\^\\*|\\>\\:P|&gt;\\:P|X\\-P|x\\-p|\\>\\:\\[|&gt;\\:\\[|\\:\\-\\(|\\:\\(|\\:\\-\\[|\\:\\[|\\=\\(|\\>\\:\\(|&gt;\\:\\(|\\>\\:\\-\\(|&gt;\\:\\-\\(|\\:@|\\:\'\\(|\\:\'\\-\\(|;\\(|;\\-\\(|\\>\\.\\<|&gt;\\.&lt;|\\:\\$|\\=\\$|#\\-\\)|#\\)|%\\-\\)|%\\)|X\\)|X\\-\\)|\\*\\\\0\\/\\*|\\\\0\\/|\\*\\\\O\\/\\*|\\\\O\\/|O\\:\\-\\)|0\\:\\-3|0\\:3|0\\:\\-\\)|0\\:\\)|0;\\^\\)|O\\:\\-\\)|O\\:\\)|O;\\-\\)|O\\=\\)|0;\\-\\)|O\\:\\-3|O\\:3|B\\-\\)|B\\)|8\\)|8\\-\\)|B\\-D|8\\-D|\\-_\\-|\\-__\\-|\\-___\\-|\\>\\:\\\\|&gt;\\:\\\\|\\>\\:\\/|&gt;\\:\\/|\\:\\-\\/|\\:\\-\\.|\\:\\/|\\:\\\\|\\=\\/|\\=\\\\|\\:L|\\=L|\\:P|\\:\\-P|\\=P|\\:\\-p|\\:p|\\=p|\\:\\-Þ|\\:\\-&THORN;|\\:Þ|\\:&THORN;|\\:þ|\\:&thorn;|\\:\\-þ|\\:\\-&thorn;|\\:\\-b|\\:b|d\\:|\\:\\-O|\\:O|\\:\\-o|\\:o|O_O|\\>\\:O|&gt;\\:O|\\:\\-X|\\:X|\\:\\-#|\\:#|\\=X|\\=x|\\:x|\\:\\-x|\\=#)'
shortcode_compiled = re.compile(ignored_regexp+"|("+shortcode_regexp+")",
                                    re.IGNORECASE)
unicode_compiled = re.compile(ignored_regexp+"|("+unicode_regexp+")",
                                  re.UNICODE)
ascii_compiled = re.compile(ignored_regexp+"|("+ascii_regexp+")",
                                re.IGNORECASE)

EMOTICONS_FILE = ('emoticons.txt') #put your emoticons file here

#urls - nltk version
URLS = r"""         # Capture 1: entire matched URL
  (?:
  https?:               # URL protocol and colon
    (?:
      /{1,3}                # 1-3 slashes
      |                 #   or
      [a-z0-9%]             # Single letter or digit or '%'
                                       # (Trying not to match e.g. "URI::Escape")
    )
    |                   #   or
                                       # looks like domain name followed by a slash:
    [a-z0-9.\-]+[.]
    (?:[a-z]{2,13})
    /
  )
  (?:                   # One or more:
    [^\s()<>{}\[\]]+            # Run of non-space, non-()<>{}[]
    |                   #   or
    \([^\s()]*?\([^\s()]+\)[^\s()]*?\) # balanced parens, one level deep: (...(...)...)
    |
    \([^\s]+?\)             # balanced parens, non-recursive: (...)
  )+
  (?:                   # End with:
    \([^\s()]*?\([^\s()]+\)[^\s()]*?\) # balanced parens, one level deep: (...(...)...)
    |
    \([^\s]+?\)             # balanced parens, non-recursive: (...)
    |                   #   or
    [^\s`!()\[\]{};:'".,<>?«»“”‘’]  # not a space or one of these punct chars
  )
  |                 # OR, the following to match naked domains:
  (?:
    (?<!@)                  # not preceded by a @, avoid matching foo@_gmail.com_
    [a-z0-9]+
    (?:[.\-][a-z0-9]+)*
    [.]
    (?:[a-z]{2,13})
    \b
    /?
    (?!@)                   # not succeeded by a @,
                            # avoid matching "foo.na" in "foo.na@example.com"
  )
"""



#my emoticons, borrowed & expanded from https://github.com/g-c-k/idiml/blob/master/predict/src/main/resources/data/emoticons.txt

EMOTICONS = []
with open(EMOTICONS_FILE, 'r') as f:
    for line in f:
        item = line.rstrip('\n')
        item = re.escape(item)
        EMOTICONS.append(item)

# Twitter specific:
HASHTAG = r"""(?:\#\w+)"""
TWITTER_USER = r"""(?:@\w+)"""
REDDIT_USER = r"(?:\/?u\/\w+)"

#separately compiled regexps
TWITTER_USER_RE = re.compile(TWITTER_USER, re.UNICODE)
REDDIT_USER_RE = re.compile(REDDIT_USER, flags=re.UNICODE)
HASHTAG_RE = re.compile(HASHTAG, re.UNICODE)
HASH_RE = re.compile(r'#(?=\w+)', re.UNICODE)
#my url version, nltk's doesn't work for separate regexp
URL_RE = re.compile(r"""((https?:\/\/|www)|\w+\.(\w{2-3}))([\w\!#$&-;=\?\-\[\]~]|%[0-9a-fA-F]{2})+""", re.UNICODE)
EMOTICON_RE = re.compile(r"""(%s)""" % "|".join(EMOTICONS), re.UNICODE)

# more regular expressions for word compilation, borrowed from nltk
#phone numbers
PHONE = r"""(?:(?:\+?[01][\-\s.]*)?(?:[\(]?\d{3}[\-\s.\)]*)?\d{3}[\-\s.]*\d{4})"""

# email addresses
EMAILS = r"""[\w.+-]+@[\w-]+\.(?:[\w-]\.?)+[\w-]"""
# HTML tags:
HTML_TAGS = r"""<[^>\s]+>"""
# ASCII Arrows
ASCII_ARROWS = r"""[\-]+>|<[\-]+"""
#long non-word, non-numeric repeats
#HANGS = r"""([^a-zA-Z0-9])\1{3,}"""
# Remaining word types:
WORDS = r"""
    (?:[^\W\d_](?:[^\W\d_]|['\-_])+[^\W\d_]) # Words with apostrophes or dashes.
    |
    (?:[+\-]?\d+[,/.:-]\d+[+\-]?)  # Numbers, including fractions, decimals.
    |
    (?:[\w_]+)                     # Words without apostrophes or dashes.
    |
    (?:\.(?:\s*\.){1,})            # Ellipsis dots.
    |
    (?:\S)                         # Everything else that isn't whitespace.
    """
TWITTER_REGEXPS = [URLS, PHONE] + EMOJIS + EMOTICONS + [HTML_TAGS, ASCII_ARROWS, TWITTER_USER, HASHTAG, EMAILS, WORDS]

REDDIT_REGEXPS = [URLS, PHONE] + EMOJIS + EMOTICONS + [HTML_TAGS, ASCII_ARROWS, REDDIT_USER, HASHTAG, EMAILS, WORDS]

WORD_RE = re.compile(r"""(%s)""" % "|".join(TWITTER_REGEXPS), re.VERBOSE | re.I | re.UNICODE) # add REDDIT_REGEXPS as necessary

def tokenize2(text):
  words = list(map((lambda x : x if EMOTICON_RE.search(x) or unicode_compiled.findall(x) else x.lower()), words))
  return words

segmenter = tinysegmenter.TinySegmenter()
from chinese_tokenizer.tokenizer import Tokenizer
jie_ba_tokenizer = Tokenizer().jie_ba_tokenizer

def new_tokenize(row):
    line = row["text"]
    tokens = tokenize2(line)
    return(tokens)

def flatten(l):
    for el in l:
        if isinstance(el, collections.Iterable) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el
            
def tknz1(row):
    line = row["text"]
    line = html.unescape(line)
    line = line.replace('\n','')
    line = line.replace('\t','')
    if row["lang"]=="ja":
        tokens = tokenize2(line)
        for i,x in enumerate(tokens):
            if  regex.findall("\p{Hiragana}|\p{Katakana}|\p{Han}",x):
                tokens[i] = segmenter.tokenize(x)
        return [x for x in flatten(tokens)]
        #tokens = segmenter.tokenize(line)
        #return tokens
    elif row["lang"]=="zh":
        tokens = tokenize2(line)
        for i,x in enumerate(tokens):
            if  regex.findall("\p{Han}",x):
                tokens[i] = segmenter.tokenize(x)
        return [x for x in flatten(tokens)]
    else:  
        tokens = line.lower()
        tokens  = tokenize2(line)
        return tokens
