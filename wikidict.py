#!/usr/bin/python3
# -*- coding: utf-8 -*-

# 1) Wiktionary Loader from dump : download the file source with HTTP (This module have one parameter : Language code)
# 2) Load into memory (TreeMap): parse the source file 
# 3) Export to 9 text file JSON UTF-8
# 4) Load from JSON text file into TreeMap
# 5) Save to disk (Pickle)
# 6) Load from disk (Pickl

# Requirements:
#   pip install blist
#   pip install wikitextparser
#   pip install requests
#
# Description:
#   blist            - The blist is a drop-in replacement for the Python list the provides better performance when modifying large lists.
#   wikitextparser   - A simple to use WikiText parsing library for MediaWiki. The purpose is to allow users easily extract and/or manipulate templates, template parameters, parser functions, tables, external links, wikilinks, lists, etc. found in wikitexts.

# Files:
# https://dumps.wikimedia.org/enwiktionary/latest/
# https://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-pages-articles.xml.bz2


import unittest
import os
import sys
import bz2
import json
import itertools
import codecs
import xml.parsers.expat
import re
import pickle
import string
import itertools
import logging
 
#import wikitextparser as wtp
from blist import sorteddict
import templates


TXT_FOLDER   = "txt"        # folder where stored text files for debugging
CACHE_FOLDER = "cached"     # folder where stored downloadad dumps
LOGS_FOLDER  = "logs"       # log folder
TEST_FOLDER  = "test"       # test folder

# logging
log_level = logging.INFO    # log level: logging.DEBUG | logging.INFO | logging.WARNING | logging.ERROR
WORD_JUST = 24              # align size

def setup_logger(logger_name, level=logging.INFO, format='%(message)s'):
    l = logging.getLogger(logger_name)

    logging.addLevelName(logging.DEBUG, "DBG")
    logging.addLevelName(logging.INFO, "NFO")
    logging.addLevelName(logging.WARNING, "WRN")
    logging.addLevelName(logging.ERROR, "ERR")

    logfile = logging.FileHandler(os.path.join(LOGS_FOLDER, logger_name+".log"), mode='w', encoding="UTF-8")
    formatter = logging.Formatter(format)
    logfile.setFormatter(formatter)
    
    console = logging.StreamHandler()
    console.setFormatter(formatter)

    l.setLevel(level)
    l.addHandler(logfile)
    
    return l

# Exception for terminate parsing on limit
class IterStopException(Exception):
    None


class WORD_TYPES:
    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adjective"
    ADVERB = "adverb"
    PRONOUN = "pronoun"
    PREPOSITION = "preposition"
    CONJUNCTION = "conjunction"
    DETERMINER = "determiner"
    EXCLAMATION = "exclamation"  
    INTERJECTION = "interjection"  
    NUMERAL = "num"
    PARTICLE = "part"
    POSTPOSITION = "postp"
    
    def detect_type(self, s):
        for a in dir(self):
            if a.isupper():
                if getattr(self, a) == s.lower():
                    return getattr(self, a)
                    
        return None # not found type
        
    def get_names(self):
        names = []
        
        for a in dir(self):
            if a.isupper():
                names.append(getattr(self, a))
                    
        return names
        

"""
Templates:
    Adjective: adj
    Adverb: adv
    Conjunction: con
    Determiner: det
    Interjection: interj
    Noun: noun
    Numeral: num
    Particle: part
    Postposition: postp
    Preposition: prep
    Pronoun: pron
    Proper noun: proper noun
    Verb: verb
"""

class Word:
    def __init__(self):
        self.LabelName = ""             #
        self.LanguageCode = ""          # (EN,FR,…)
        self.Type = ""                  #  = noun,verb… see = WORD_TYPES
        self.TypeLabelName = ""         # chatt for verb of chat
        self.ExplainationExample = [ ]  # (explaination1||Example1) (A wheeled vehicle that moves independently||She drove her car to the mall..)
        self.IsMaleVariant = None
        self.IsFemaleVariant = None
        self.MaleVariant = None         # ""
        self.FemaleVariant = None       # ""
        self.IsSingleVariant = None
        self.IsPluralVariant = None
        self.SingleVariant = None       # ""
        self.PluralVariant = None       # ""
        self.AlternativeFormsOther = [] # (British variant, usa variant, etc…)
        self.RelatedTerms = None        # [] (list of all Related terms and Derived terms)
        self.IsVerbPast = None
        self.IsVerbPresent = None
        self.IsVerbFutur = None
        self.Conjugation = None         # [ ] (All verb Conjugation (example = like, liking, liked)
        self.Synonyms = None            # [ ]
        self.Translation_EN = None      # [ ]
        self.Translation_FR = None      # [ ]
        self.Translation_DE = None      # [ ]
        self.Translation_ES = None      # [ ]
        self.Translation_RU = None      # [ ]
        self.Translation_CN = None      # [ ]
        self.Translation_PT = None      # [ ]
        self.Translation_JA = None      # [ ]

    def save_to_json(self, filename):
        save_to_json(self, filename)

    def save_to_pickle(self, filename):
        save_to_pickle(self, filename)

    def __repr__(self):
        return "Word("+self.LabelName+")"


class WordsEncoder(json.JSONEncoder):
    """
    This class using in JSON encoder.
    Take object with Word objects and return dict.
    """
    def default(self, obj):
        if isinstance(obj, Word):
            # Word
            return {k:v for k,v in obj.__dict__.items() if k[0] != "_"}

        elif isinstance(obj, sorteddict):
            # sorteddict
            return dict(obj.items())

        # default
        return json.JSONEncoder.default(self, obj)


def create_storage(folder_name):
    """
    Create folders recusively.

    In:
      folder_name: Storage folder name

    """
    if (not os.path.exists(folder_name)):
        os.makedirs(folder_name, exist_ok=True)
        
def sanitize_filename(filename):
    """
    Remove from string 'filename' all nonascii chars and  punctuations.
    """
    filename = str(filename).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', filename)

def unique(lst):    
    return list(set(lst))

def get_contents(filename):
    """
    Read the file 'filename' and return content.
    """
    with open(filename, encoding="UTF-8") as f:
        return f.read()
        
    return None

def put_contents(filename, content):
    """
    Save 'content' to the file 'filename'. UTF-8.
    """
    with open(filename, "w", encoding="UTF-8") as f:
        f.write(content)

def save_text(label, text, ext=".txt"):
    """
    Save string 'text' into the file TXT_FOLDER/<label>.txt
    """
    put_contents(os.path.join(TXT_FOLDER, sanitize_filename(label) + ext), text)
    
def save_to_json(treemap, filename):
    """
    Save 'treemap' in the file 'filename'. In JSON format. Encoding UTF-8.
    """
    create_storage(os.path.dirname(os.path.abspath(filename)))
    
    with open(filename, "w", encoding="UTF-8") as f:
        json.dump(treemap, f, cls=WordsEncoder, sort_keys=False, indent=4, ensure_ascii=False)

def load_from_json(filename):    
    """
    Load data from JSON-file 'filename'. Decode to class Word. Encoding UTF-8. 
    
    In:
        filename
    Out:
        sorteddict | None
    """
    def decode_json_object(obj):
        """
        json object decoder callback.
        """
        if "LabelName" in obj:
            word = Word()
            
            for k,v in obj.items():
                setattr(word, k, v)
            
            return word
            
        else:
            return sorteddict(obj)        

    # decode
    with open(filename, "r", encoding="UTF-8") as f:
        treemap = json.load(f, object_hook=decode_json_object)
        return treemap
        
    return None

def save_to_pickle(treemap, filename):    
    """
    Save Treemap to the 'filename' in Pickle format.
    
    In:
        treemap
        filename
    """
    create_storage(os.path.dirname(os.path.abspath(filename)))
    
    with open(filename, "wb") as f:
        pickle.dump(treemap, f)

def load_from_pickle(filename):    
    """
    Load Treemap from the file 'filename'. File must be in Pickle format.
    
    In:
        filename
    Out:
        sorteddict
    """
    with open(filename, "rb") as f:
        obj = pickle.load(f, encoding="UTF-8")
        return obj

    return None

def is_english(s):
    """
    Check word for all chars is English.
    
    In:
        s - string
    Out:
        True | False
    """
    try:
        s.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True


class Wikidict:
    """
    This is the main class.
        # 1) Wiktionary Loader from dump : download the file source with HTTP (This module have one parameter : Language code)
        # 2) Load into memory (TreeMap): parse the source file 
        # 3) Export to 9 text file JSON UTF-8
        # 4) Load from JSON text file into TreeMap
        # 5) Save to disk (Pickle)
        # 6) Load from disk (Pickle)
    """
    def __init__(self):
        self.limit = 0 # all
        self.treemap = sorteddict()
        self.is_need_save_txt = False
        
    def download(self, lang="en", use_cached=True):
        """
        Download file from HTTPS.
        
        In:
            lang       - Language code string, like a: en, de, fr
            use_cached - True if need use cached_file. False for force run downloading.
        Out:
            local_file - local cached file name
        """
        remote_file = "https://dumps.wikimedia.org/"+lang+"wiktionary/latest/"+lang+"wiktionary-latest-pages-articles.xml.bz2"
        
        create_storage(CACHE_FOLDER)
        local_file = os.path.join(CACHE_FOLDER, lang+"wiktionary-latest-pages-articles.xml.bz2")

        # check cache
        if use_cached and os.path.exists(local_file):
            return local_file

        # download
        import requests
        import shutil
                
        r = requests.get(remote_file, auth=('usrname', 'password'), verify=False,stream=True)
        r.raw.decode_content = True
        
        log.info("Downloading....")
        with open(local_file, 'wb') as f:
            shutil.copyfileobj(r.raw, f)  
        log.info("Downloaded....[ OK ]")
        
        return local_file
    
    def parse_dump(self, dump_file):
        """
        Parse 'dump_file'.
        Here:
        - unzip bz2 file
        - parse xml
        - extract <page>
        - extract <label>, <text>
        - parse text
        - create Word
        - fill Word with data
        
        Extracted words saved in sorteddict self.treemap.
        Can limit of words extraction by call set_limit(N), Like a set_limit(100).
        
        In:
            dump_file - string contans local file name, like a "./ru/ruwiktionary-latest-pages-articles.xml.bz2"
        Out:
            treemap - sorteddict with words, like a: {'chat': [Word, Word, Word]}
        """
        # dump_file = "./ru/ruwiktionary-latest-pages-articles.xml.bz2"
        self.text_parser = TextParser()
        self.text_parser.is_need_save_txt = self.is_need_save_txt
        self.count = 0
        self.treemap = sorteddict()
        
        def callback(label, text):
            # keep english words only
            if not is_english(label):
                #put_contents(os.path.join(TXT_FOLDER, sanitize_filename("non_english-"+label)+".txt"), text)
                log_non_english.warning("%s: non english chars ... [SKIP]", label.ljust(WORD_JUST))
                return
            
            # main step
            words = self.text_parser.parse(label, text)
            self.treemap[label] = words

            #
            self.count += 1
            
            if self.count % 100 == 0:
                log.info("%d", self.count)

            if self.limit and (self.count > self.limit):
                raise IterStopException()

        try: read_dump(dump_file, callback)
        except IterStopException: return
        
        return self.treemap
        
    def set_limit(self, n):
        """
        Set limit on word extraction, 'n' words only.
        """
        self.limit = n
        
    def get_all_dump_sections(self, dump_file):
        """
        Debugging function for extract all section names, like ==English==, ==Middle English==, ...
        """
        # dump_file = "./ru/ruwiktionary-latest-pages-articles.xml.bz2"
        self.text_parser = SectionExtractor()        
        self.count = 0
        
        def callback(label, text):
            words = self.text_parser.parse(label, text)
            
            self.count += 1
            
            if self.count % 1000 == 0:
                log.info("%d", self.count)

            if self.limit and self.count > self.limit:
                with open("sections.txt", "w", encoding="UTF-8") as f:
                    for x in self.text_parser.sections.keys():
                        f.write(x+"\n")
                raise IterStopException()

        try: read_dump(local_file, callback)
        except IterStopException: return self.text_parser.sections.keys()
        
        return self.text_parser.sections.keys()


class SectionExtractor:
    """
    Class for debugging, for extract section names.
    """
    def __init__(self):
        self.sections = {}
        
    def parse(self, label, text):
        parsed = wtp.parse(text)
        
        for section in parsed.sections:
            self.sections[section.title] = 1
            

def read_dump(dump_file, text_callback):
    """
    Read .bz2 file 'dump_file', parse xml, call 'text_callback' on each <page> tag.
    Callback format: text_callback(label, text)
    """
    stream = bz2.BZ2File(dump_file, "r")
    parser = XMLParser()
    parser.parse(stream, text_callback)
    stream.close()


class XMLParser:
    """
    XML parser. Parser xml stream, find <page>, extract all subtags and data, and run callback.
    """
    def __init__(self):
        self.inpage = False
        self.intitle = False
        self.intext = False
        self.title = ""
        self.text = ""
     
        ### BEGIN ###
        # Initializing xml parser
        self.parser = xml.parsers.expat.ParserCreate()
        
        self.parser.StartElementHandler = self.start_tag
        self.parser.EndElementHandler = self.end_tag
        self.parser.CharacterDataHandler = self.data_handler
        self.parser.buffer_text = True
        self.parser.buffer_size = 1024

    def start_tag(self, tag, attrs):
        #print("  " * len(self.opened), tag)
        
        if not self.inpage:
            if tag == "page":
                self.inpage = True
                self.intitle = False
                self.intext = False
                self.text = ""
                self.title = ""
                
        elif self.inpage:
            if tag == "title":
                self.intitle = True
                self.title = ""
                
            elif tag == "text":
                self.intext = True
                self.text = ""
                
    def data_handler(self, data):
        if self.inpage:
            if self.intitle:
                self.title += data
                
            elif self.intext:
                self.text += data

    def end_tag(self, tag):
        if self.inpage:
            if tag == "page":
                self.page_callback(self.title, self.text)
                self.inpage = False

            elif tag == "title":
                self.intitle = False
                
            elif tag == "text":
                self.intext = False

    def parse(self, file_stream, page_callback):
        """
        Parse xml stream 'file_stream', and run callback 'page_callback'
        
        In:
            file_stream   - stream like a: File
            page_callback - function like a: page_callback(label, text)
            
        """
        self.page_callback = page_callback

        log.info("Processing...")
        self.parser.ParseFile(file_stream)
        log.info("Done processing.")


def oneof(*args):
    it_was = False
    
    for gen in args:
        if gen:
            for a in gen:
                it_was = True
                yield a
                
            if it_was:
                break

def cleanup(s):
    # remove brackets like a [[...]]
    # remove templates
    
    # remove ###
    i = 0
    l = len(s)
    if l > 0 and s[0] in "#*":
        while i < l and s[i] in "#*: ":
            i += 1
        
        s = s[i:]
        
    # extract from brackets, like a [[ text ]]
    s = s.replace("[[", "").replace("]]", "")

    # extract from brackets, like a ''' text '''
    s = s.replace("'''", "")

    # extract from brackets, like a '' text ''
    s = s.replace("''", "'")

    # remove head and tail spaces
    s = s.strip()

    return s


############################ NEW VERSION OF PARSER ################################
import wikoo    


def get_explainations(section):
    explainations = []
    
    for li in section.find_lists():
        #print(li.data)
        #print(li, li.is_empty(), li.has_templates_only())
        # ... scan list
        if li.has_templates_only():
            # check subtemplate
            for sub in li.find_lists():
                if sub.has_templates_only():
                    continue
                else:
                    # OK. add
                    explainations.append(sub.get_text())
        else:
            if li.base.endswith(":"):
                # skip example
                pass
            else:
                # OK. add
                explainations.append(li.get_text())
        
    return explainations
    
def get_alternatives(section):
    # ==English== section here
    # ===Alternative forms===
    # * {{l|en|hower}} {{qualifier|obsolete}}
    
    result = []
    
    for sec in section.find_section_recursive("Alternative forms"):
        for t in sec.find_templates_recursive():
            # * {{l|en|hower}}
            if t.name == "l":
                lang = t.arg(0)
                term = t.arg(1)
                
                if term:
                    result.append( (lang, term) )
        
    #
    bylang = {}
    
    #
    for lang, term in result:
        if lang in bylang:
            bylang[lang].append(term)
        else:
            bylang[lang] = []
            bylang[lang].append(term)

    return bylang

def get_related(section):
    # print(dir(t))
    # {{rel-top|related terms}}
    #   * {{l|en|knight}}
    #
    # {{rel-top|related terms}}
    # * {{l|en|knight}}
    
    
    #s = "{{rel-top|related terms}}"
    #lst = self.get_list_after_string(parsed, s)
    
    result = []
    
    found = False
    pos = 0
    
    # case 1
    # {{rel-top|related terms}}
    # * {{l|en|knight}}, {{l|en|cavalier}}, {{l|en|cavalry}}, {{l|en|chivalry}}
    # * {{l|en|equid}}, {{l|en|equine}}
    # * {{l|en|gee}}, {{l|en|haw}}, {{l|en|giddy-up}}, {{l|en|whoa}}
    # * {{l|en|hoof}}, {{l|en|mane}}, {{l|en|tail}}, {{l|en|withers}}
    # {{rel-bottom}}
    
    # get next list 
    # get templates {{l|...}}
    
    for obj in section.find_objects_between_templates_recursive("rel-top", "rel-bottom", "related terms"):
        if isinstance(obj, wikoo.LI):
            for t in obj.find_templates():
                if t.name == "l":
                    lang = t.arg(0)
                    term = t.arg(1)
                    
                    if term:
                        result.append( (lang, term) )

    # case 2
    # {{rel-top|related terms}}
    for sec in section.find_section_recursive("Related terms"):
        for t in sec.find_templates_recursive():
            # * {{l|en|hower}}
            if t.name == "l":
                lang = t.arg(0)
                term = t.arg(1)
                
                if term:
                    result.append( (lang, term) )
                    
    #
    bylang = {}
    
    #
    for lang, term in result:
        if lang in bylang:
            bylang[lang].append(term)
        else:
            bylang[lang] = []
            bylang[lang].append(term)

    return bylang
    
def get_translations(section):
    # case 1
    # =====Translations=====
    # {{trans-top|members of the species ''Equus ferus''}}
    # * ...
    # {{trans-bottom}}
    
    result = []

    for obj in section.find_objects_between_templates_recursive("trans-top", "trans-bottom"):
        if isinstance(obj, wikoo.LI):
            for t in obj.find_templates():
                # {{t-simple|za|max|langname=Zhuang}}
                if t.name.lower() == "t-simple":
                    lang = t.arg(0)
                    term = t.arg(1)
                    
                    if term:
                        result.append( (lang, term) )
                            
                elif t.name.lower() == "t+":
                    # {{t+|zu|ihhashi|c5|c6}}
                    lang = t.arg(0)
                    term = t.arg(1)
                    
                    if term:
                        result.append( (lang, term) )
                            
                elif t.name.lower() == "t":
                    # {{t|ude|муи }}
                    lang = t.arg(0)
                    term = t.arg(1)
                    
                    if term:
                        result.append( (lang, term) )

    #
    bylang = {}
    
    #
    for lang, term in result:
        if lang in bylang:
            bylang[lang].append(term)
        else:
            bylang[lang] = []
            bylang[lang].append(term)

    return bylang

def get_synonyms(section):
    """
    ==English==
    ===Etymology 1===
    ====Noun====
    =====Synonyms=====
    * {{sense|animal}} {{l|en|horsie}}, {{l|en|nag}}, {{l|en|steed}}, {{l|en|prad}}
    * {{sense|gymnastic equipment}} {{l|en|pommel horse}}, {{l|en|vaulting horse}}
    * {{sense|chess piece}} {{l|en|knight}}
    * {{sense|illegitimate study aid}} {{l|en|dobbin}}, {{l|en|pony}}, {{l|en|trot}}

    ====Synonyms====
    * {{sense|period of sixty minutes|a season or moment}} {{l|en|stound}} {{qualifier|obsolete}}
    """
    
    result = []
    
    # here is section like a ====Noun==== or ====Verb====
    # find section =====Synonyms=====
    for sec in section.find_section_recursive("Synonyms"):
        for t in sec.find_templates_recursive():
            # find {{sense|animal}} | {{l|en|horsie}}
            # remove brackets like a [[...]]
            # remove templates
            # get example
            if 0 and t.name == "sense": # disabled, because words only
                    lang = t.arg(0)
                    term = t.arg(1)
                    
                    if term:
                        result.append( (lang, term) )
                
            elif t.name == "l":
                    lang = t.arg(0)
                    term = t.arg(1)
                    
                    if term:
                        result.append( (lang, term) )
    
    #
    bylang = {}
    
    #
    for lang, term in result:
        if lang in bylang:
            bylang[lang].append(term)
        else:
            bylang[lang] = []
            bylang[lang].append(term)

    return bylang
    
def get_conjugations(section):
    """
    ==English==
    ===Etymology 1===
    ====Verb====
    =====Conjugation=====
    {{en-conj|do|did|done|doing|does}}

    In: section Verb
    
    Out:
        [ basic, simple_past, past_participle, present_participle, simple_present_third_person ]
    """
    
    result = []
    
    # here is section ====Verb====
    for t in section.find_templates_recursive():
        if t.name == "en-conj":
            result += templates.en_conj(t, label)
            
        elif t.name == "en-verb":
            (third, present_participle, simple_past, past_participle) = templates.en_verb(t, label)
            result.append(third)
            result.append(present_participle)
            result.append(simple_past)
            result.append(past_participle)

    # unique
    result = unique(result)
    
    return result if result else None

def is_male_variant(section):
    # From {{inh|en|enm|cat}}, {{m|enm|catte}}, 
    # from {{inh|en|ang|catt||male cat}}, {{m|ang|catte||female cat}}, 
    # from {{inh|en|gem-pro|*kattuz}}.
    for t in section.find_templates_recursive():
        if t.name == "ang-noun":
            (head, gender, plural, plural2) = templates.ang_noun(t, label)
            
            if gender == "m":
                return True
                
    return None

def is_female_variant(section):
    # From {{inh|en|enm|cat}}, {{m|enm|catte}}, 
    # from {{inh|en|ang|catt||male cat}}, {{m|ang|catte||female cat}}, 
    # from {{inh|en|gem-pro|*kattuz}}.
    for t in section.find_templates_recursive():
        if t.name == "ang-noun":
            (head, gender, plural, plural2) = templates.ang_noun(t, label)
            
            if gender == "f":
                return True
                
    return None

def is_singular(section):
    for t in section.find_templates_recursive():
        if t.name == "en-noun":
            (s, p, is_uncountable) = templates.en_noun(t, label)
            
            if p:
                return True

    return None

def is_plural(section):
    # {{plural of|cat|lang=en}}
    for t in section.find_templates_recursive():
        if t.name == "plural of":
            #(lang, single, showntext) = templates.plural_of(t, label)            
            return True
    
    return None
    
def is_verb_present(section, label):
    # {{present participle of}}
    for t in section.find_templates_recursive():
        if t.name == "present participle of":
            return True
            
    return None

def is_verb_past(section, label):
    # {{en-past of}}
    for t in section.find_templates_recursive():
        if t.name == "en-past of":
            return True
            
    return None

def is_verb_futur(section, label):
    return None

def get_singular_variant(section, label):
    return None

def get_plural_variant(section, label):
    for t in section.find_templates_recursive():
        if t.name == "ang-noun":
            (head, gender, plural, plural2) = templates.ang_noun(t, label)
            
            if plural is not None:
                return plural

        elif t.name == "en-noun":
            (single, plural, is_uncountable) = templates.en_noun(t, label)

            if plural:
                return plural
                
    return None

def get_words(label, text):
    # get section ==English==
    # if not: get root
    # for each section Noun | Verb | ...
    #   get list. first list only
    #     get explainations
    #
    words = []
    
    root = wikoo.parse(text)
    
    #    
    for english_section in oneof(root.find_section("English"), [root]):
        # common alternatives
        common_alternatives = get_alternatives(english_section).get("en", None)

        # common translations
        common_translations = get_translations(english_section)

        # by types
        for section in oneof(english_section.find_sections_recursive( WORD_TYPES().get_names() ), [english_section]):
            #print(english_section, section)
            # word
            word = Word()
            words.append(word)
            
            # label
            word.LabelName = label
            
            # lang
            word.LanguageCode = "en"
            
            # type
            word.Type = WORD_TYPES().detect_type(section.title)
            word.TypeLabelName = section.title
            
            # explainations
            word.ExplainationExample = [
                    {"cln":cleanup(expl), "raw":expl} for expl in get_explainations(section)
                ]
        
            # alternatives
            # type alternatives
            #type_alternatives = get_alternatives(section)
            word.AlternativeFormsOther = common_alternatives

            # relates
            word.RelatedTerms = get_related(section).get("en", None)
            
            # translations
            #type_translations = get_translations(section)
            word.Translation_EN = common_translations.get("en", None)
            word.Translation_FR = common_translations.get("fr", None)
            word.Translation_DE = common_translations.get("de", None)
            word.Translation_ES = common_translations.get("es", None)
            word.Translation_RU = common_translations.get("ru", None)
            word.Translation_CN = common_translations.get("cn", None)
            word.Translation_PT = common_translations.get("pt", None)
            word.Translation_JA = common_translations.get("ja", None)
            
            # translations
            word.Synonyms = get_synonyms(section).get("en", None)
            
            # conjugations
            word.Conjugation = get_conjugations(section)
            
            # male | female
            if is_male_variant(section):
                word.IsMaleVariant = True

            if is_female_variant(section):
                word.IsFemaleVariant = True

            # singular | plural
            if is_singular(section):
                word.IsSingleVariant = True
            
            # single variant
            single = get_singular_variant(section, label)
            
            if single is not None:
                word.SingleVariant = single
            
            # plural variant
            plural = get_plural_variant(section, label)
            
            if plural is not None:
                word.PluralVariant = plural
                
            # verb
            word.IsVerbPresent = is_verb_present(section, label)
            word.IsVerbPast = is_verb_past(section, label)
            word.IsVerbFutur = is_verb_futur(section, label)
            
    # JSON
    #save_to_json( words, os.path.join( TEST_FOLDER, label+".json" ) )
    #exit(0)
     
    return words

label = "cat"
text = """
==English== 

===Verb===
{{noun}}

# {{expl1}}
# {{expl2}}
## expl2-1
# expl3 {{tpl|aaa {{sub}} }} {{second|1|2|3}} tail
"""

#label = "do"
#text = get_contents( os.path.join( TEST_FOLDER, label+".txt" ) )
#root = wikoo.parse(text)
#get_words(label, text)
#exit(0)

############################## </NEW VERSIOM> ##############################


class TextParser:
    """
    Wikitionary text Parser
    
    It parse the text in Wikitionary format, like a: 
        {{also|Chat|chất|chắt|chặt|chật}}
        ==English==
        {{wikipedia}}

        ===Pronunciation===
        * {{IPA|/tʃæt/|lang=en}}
        * {{audio|en-us-chat.ogg|Audio (US)|lang=en}}
        * {{audio|EN-AU ck1 chat.ogg|Audio (AU)|lang=en}}
        * {{rhymes|æt|lang=en}}

        ===Etymology 1===
        Abbreviation of {{m|en|chatter}}. The bird sense refers to the sound of its call.

        ====Verb====
        {{en-verb|chatt}}
        [[image:Wikimania 2009 - Chatting (3).jpg|thumb|Two people '''chatting'''. (1) (2)]]

        # To be [[engage]]d in informal [[conversation]].
        #: {{ux|en|She '''chatted''' with her friend in the cafe.}}
        #: {{ux|en|I like to '''chat''' over a coffee with a friend.}}
    
    """
    def __init__(self):
        self.is_need_save_txt = False
        
    def parse(self, label, text):
        if self.is_need_save_txt:
            save_text(label, text)
        
        root = wikoo.parse(text)
        words = get_words(label, text)
        return words
    
    def parse2(self, label, text):
        """
        Parse 'text' for word 'label'.
        Extract:
        - language
        - word type: noun, verb
        - explainations
        - sections
        - alternatives
        - relates
        - translations
        - synonyms
        - conjugations
        - singular | plural
        
        In:
            label - string, word label
            text  - string, word article from wikitionary
        Out:
            words - list of extracted words, like a: [Word, Word, Word]
        """    
        log.debug("'%s'", label)
        
        words = []
    
        # Parse text
        parsed = wtp.parse(text)

        # ==English==
        lang_sections = self.get_langs(parsed)
        
        if len(lang_sections) == 0:
            # fix
            (parsed, text, lang_sections) = self.fix_add_english_section(parsed, text, lang_sections)
            log.debug("%s: not found section ==English== ... [FIXED]", label.ljust(WORD_JUST))
            #save_text(label, text)

        # each language: English | MiddleEnglish
        for (lang, lang2, lang_title, lsection) in lang_sections:
            # get types
            #   (noun, section),
            #   (verb, section),
            #   (adjective, section)
            types           = self.get_types(lsection)
            alternatives    = self.get_alternatives(lsection)
            
            if len(lang_sections) == 0:
                log.warning("%s: not found section Verb | Noun ... [SKIP]", label.ljust(WORD_JUST))

            # each type. noun|verb
            for (tcode, ttitle, tsection) in types:
                is_female_variant = None
                is_single_variant = None
                is_plural_variant = None
                is_verb_past      = None
                is_verb_present   = None
                is_verb_futur     = None
                male_variant      = None
                female_variant    = None
                single_variant    = None
                plural_variant    = None
                conjugations      = []

                if tcode == WORD_TYPES.NOUN:
                    forms = self.template_en_noun(tsection, label)
                    if forms:
                        (single_variant, plural_variant) = forms
                    
                elif tcode == WORD_TYPES.VERB:
                    forms = self.template_en_verb(tsection, label)
                    if forms:                    
                        (label_third, label_present_participle, label_simple_past, label_past_participle) = forms
                        
                    conjugations = self.get_conjugations(tsection, label)
                    
                    if not conjugations:
                        conjugations = [label_third, label_present_participle, label_simple_past, label_past_participle]                
                    
                elif tcode == WORD_TYPES.ADJECTIVE:
                    conjugations = self.template_en_adj(tsection, label)
                    conjugations += self.template_li_adj(tsection, label)
                    conjugations = [x for x in conjugations if x]
                    
                elif tcode == WORD_TYPES.ADVERB:
                    conjugations = self.template_en_adv(tsection, label)
                    conjugations = [x for x in conjugations if x]
                    
                explainations   = self.get_explainations(tsection)
                related         = self.get_related(tsection)
                synonyms        = self.get_synonyms(tsection)
                translations    = self.get_translations(tsection)
                is_plural       = self.get_is_plural(tsection)
                is_male_variant = self.get_is_male_variant(tsection)
                
                # fix
                if len(explainations) == 0:
                    explainations.append( ("", 0, "", "", []) )

                # for each explaination
                for (expl_lang, level, explaination, raw_explaination, examples) in explainations:
                    word = Word()
                    
                    self.setup_word(word, 
                        label, lang, lang2, lang_title, tcode, 
                        {"exp": explaination, "raw": raw_explaination},
                        is_male_variant, is_female_variant,
                        male_variant, female_variant,
                        is_single_variant, 
                        len([x for x in is_plural if x[1]]) > 0 , # [(lang, True)]
                        single_variant, plural_variant,
                        [x[1] for x in alternatives],
                        related,
                        is_verb_past, is_verb_present, is_verb_futur,
                        unique(conjugations), # unique
                        [x_string for (x_lang, x_string) in synonyms if x_lang is None or x_lang == lang],
                        translations
                        )
                        
                    words.append(word)
        
        return words

        
    def get_sentences(self, section, label):
        """
        https://en.wiktionary.org/wiki/Wiktionary:Entry_layout#Headword_line
        https://en.wiktionary.org/wiki/Wiktionary:Example_sentences
        
        # Sentence
        #: Example
        
        #
        ## Sentence
        ##: Example

        # {{lb|en|of people}}
        ## Acting in the interest of what is [[beneficial]], [[ethical]], or [[moral]].
        ##: {{ux|en|'''good''' intentions}}
        ##* '''1460-1500''', ''The Towneley Plays''ː
        ##*: It is not '''good''' to be alone, to walk here in this worthly wone.
        ##* '''1500?''', [http://quod.lib.umich.edu/cgi/m/memem/memem-idx?fmt=entry&type=entry&byte=66789 Evil Tongues]ː
        ##*: If any man would begin his sins to reny, or any '''good''' people that frae vice deed rest ain. What so ever he were that to virtue would apply, But an ill tongue will all overthrow again.
        ##* '''1891''', {{w|Oscar Wilde}}, ''{{w|The Picture of Dorian Gray}}'', Ch.6
        ##*: When we are happy, we are always '''good''', but when we are '''good''', we are not always happy.
        ## [[competent|Competent]] or [[talent]]ed.
        ##: {{ux|en|a '''good''' swimmer}}
        ##* {{quote-book|lang=en|1704|{{w|Robert South}}|Twelve Sermons Preached on Several Occasions|||Flatter him it may, I confess, (as those are generally '''good''' at flattering who are '''good''' for nothing else,) but in the meantime the poor man is left under the fatal necessity of a needless delusion|section=On the nature and measure of conscience}}
        ##* {{quote-book|lang=en|year=1922|author={{w|Michael Arlen}}|title=[http://openlibrary.org/works/OL1519647W “Piracy”: A Romantic Chronicle of These Days]|chapter=3/19/2
        |passage=Ivor had acquired more than a mile of fishing rights with the house ; he was not at all a '''good''' fisherman, but one must do something ; one generally, however, banged a ball with a squash-racket against a wall.}}
        ##* '''2016''', [https://web.archive.org/web/20170918070146/https://learningenglish.voanews.com/a/lets-learn-english-lesson-3-i-am-here/3126527.html VOA Learning English] (public domain)
        """
        # get
        result = []
        
        def is_template_only(s):
            ss = s.strip()
            ss = ss.lstrip("#*:\n\r\t ")
            
            if ss.startswith("{{") and ss.endswith("}}"):
                return True
            else:
                return False
        
        def get_sentences_req(tree, result):
            if tree:
                for i,line in enumerate(tree):
                    if isinstance(line, list):
                        # sublist
                        get_sentences_req(line, result)
                        
                    else:
                        # string
                        if is_template_only(line):
                            # get sentence from sublist
                            if len(tree) > i+1:
                                next = tree[i+1]
                                if isinstance(next, list):
                                    get_sentences_req(tree[i+1:], result)
                                else:
                                    continue
                            
                        else:
                            # found
                            if line.startswith("# ") or line.startswith("## ") or line.startswith("### "):
                                result.append(line)

        #
        for lst in section.lists():
            tree = self.parse_list(lst.string.split("\n"))
            get_sentences_req(tree, result)
            break # first only
            
        return result
            
    def template_ux(self, section, label):
        """
        https://en.wiktionary.org/wiki/Template:ux
        
        {{ux}}
        """
        pass
    
    def template_head(self, section, label):
        """
        https://en.wiktionary.org/wiki/Wiktionary:Entry_layout#Headword_line
        https://en.wiktionary.org/wiki/Wiktionary:Templates#Headword-line_templates
        https://en.wiktionary.org/wiki/Template:head
        
        {{head|nds-nl|adjective}}
        {{head|ms|noun|Jawi spelling|چت}}
        
        Out:
            "label"
        """
        pass
        
    def template_en_noun(self, section, label):
        """
        {{en-noun}}
        {{en-noun|es}}
        {{en-noun|...}}
        {{en-noun|...|...}}
        
        Out:
            (singular, plural)
        """
        label_s = label
        label_p = None
        
        for template in section.templates:
            if template.name == "en-noun":
                hasPlural, addAll = False, False
                for key, value in self.get_named_args(template):
                    if key.startswith("pl"):
                        label_p = value
                        hasPlural = True

                # http://en.wiktionary.org/wiki/Template:en-noun
                acount = self.get_positional_arg_count(template)
                if acount == 0:
                    if not hasPlural:
                        label_p = label + "s"
                elif acount == 1:
                    param1 = self.get_positional_arg(template, 0)
                    if "-" == param1:
                        label_p = "" # uncountable
                    elif "~" == param1:
                        label_p = label + "s"  # countable and uncountable
                    elif "!" == param1:
                        log_unsupported.warning("%s: not attested template: %s", label.ljust(WORD_JUST), template.string)  # not attested
                    elif "?" == param1:
                        log_unsupported.warning("%s: unsupported template: %s", label.ljust(WORD_JUST), template.string)  # unknown
                    else:
                        label_p = label + param1
                elif acount == 2:
                    param1 = self.get_positional_arg(template, 0)
                    param2 = self.get_positional_arg(template, 1)
                    if "-" == param1:
                        label_p = label + param2  # usually uncountable
                    elif "-" == param2:
                        label_p = label + param1  # countable and uncountable
                    elif "!" == param1:
                        log_unsupported.warning("%s: not attested template: %s", label.ljust(WORD_JUST), template.string)  # not attested
                    elif "?" == param1:
                        log_unsupported.warning("%s: unknown forms. template: %s", label.ljust(WORD_JUST), template.string)  # unknown
                        # unknown. skip
                    elif "?" == param2:
                        label_p = label + param1  # unknown
                    elif "ies" == param2:
                        label_p = param1 + param2  # unknown
                    else:
                        addAll = True
                
                if addAll or acount > 2:
                    length = self.get_positional_arg_count(template)
                    inserted = False
                    for i in range(length):
                        param = self.get_positional_arg(template, i)
                        if param is None or "~" == param:
                            continue

                        if "s" == param or "es" == param:
                            label_p = label + param
                        elif "" == param:
                            if not inserted:
                                label_p = label + "s"
                        else:
                            label_p = param
                        inserted = True
                        
        return (label_s, label_p)
        
    def template_en_interj(self, section, label):
        """
        https://en.wiktionary.org/wiki/Template:en-interj
        {{en-interj}}
        
        Out:
            []
        """
        # skip. because as is
        
        return []


    def template_en_adv(self, section, label):
        """
        https://en.wiktionary.org/wiki/Template:en-adv
        {{en-adv|better|sup=best}}
        
        Out:
            [comparative, superlative]
        """
        result = []
        
        for template in section.templates:
            if template.name == "en-adv":
                acount = self.get_positional_arg_count(template)

                comparative = None
                superlative = None

                if acount == 0:
                    pass
                    
                if acount == 1:
                    param1 = self.get_positional_arg(template, 0)
                    
                    if param1 == "er":
                        comparative  = label + "er"
                        superlative  = label + "est"
                        
                    elif param1 == "more":
                        comparative  = "more " + label
                        superlative  = "most " + label
                        
                    elif param1 == "further":
                        comparative  = "further " + label
                        superlative  = "furthest " + label
                        
                    elif param1 == "+":
                        comparative  = "further " + label
                        superlative  = None
                        
                    elif param1 == "-":
                        # not comparative
                        continue
                        
                    elif param1 == "?":
                        # unknown forms. skip
                        continue
                        
                    else:
                        comparative  = param1
                        
                        if label.endswith("er"):
                            superlative  = label[:-2] + "est"
                        else:
                            superlative  = label + "est"
        
                elif acount == 2:
                    param1 = self.get_positional_arg(template, 0)
                    param2 = self.get_positional_arg(template, 1)
                    comparative  = param1
                    superlative  = param2

                # sup
                if len(self.get_named_args(template)) >= 1:
                    sup = self.get_named_arg(template, "sup")
                    if sup and acount >= 1:
                        comparative  = self.get_positional_arg(template, 0)
                        superlative  = sup
                        result.append( comparative )
                        result.append( superlative )
                        
                    sup2 = self.get_named_arg(template, "sup1")
                    if sup2 and acount >= 2:
                        comparative  = self.get_positional_arg(template, 1)
                        superlative  = sup2
                        result.append( comparative )
                        result.append( superlative )
                        
                    sup3 = self.get_named_arg(template, "sup2")
                    if sup3 and acount >= 3:
                        comparative  = self.get_positional_arg(template, 2)
                        superlative  = sup3
                        result.append( comparative )
                        result.append( superlative )
                        
                    sup4 = self.get_named_arg(template, "sup3")
                    if sup4 and acount >= 4:
                        comparative  = self.get_positional_arg(template, 3)
                        superlative  = sup4
                        result.append( comparative )
                        result.append( superlative )
                    
                else:
                    result.append( comparative )
                    result.append( superlative )
                
        return result    
    
    def template_li_adj(self, section, label):
        """
        https://en.wiktionary.org/wiki/Template:li-adj
        irregular adjectives has named params
        {{ li-adj }}
        {{ li-adj | comp=buugzamer }}
        {{ li-adj | comp=helder | sup2=hèls }}
        {{ li-adj | stem=aaj }}
        {{ li-adj | stem=vèt | comp=vètter }}
        
        comparative, superlative, predicate 
        """        
        result = []
        
        for template in section.templates:
            if template.name == "li-adj":
                comp = self.get_named_arg(template, "comp")
                sup  = self.get_named_arg(template, "sup")
                sup2 = self.get_named_arg(template, "sup2")
                stem = self.get_named_arg(template, "stem")
                
                result = [x for x in [comp, sup, sup2, stem] if x]
            
        return result
        
    def template_en_adj(self, section, label):
        """
        https://en.wiktionary.org/wiki/Template:en-adj
        {{en-adj}}
        {{en-adj|more}}
        {{en-adj|er}}
        {{en-adj|er|more}}
        {{en-adj|er|shyer}}
        {{en-adj|hotter}}
        {{en-adj|better|sup=best}}
        {{en-adj|shorter-lived|sup=shortest-lived}}
        {{en-adj|-}}
        {{en-adj|-|er}}
        {{en-adj|?}}
        {{en-adj|+}}
        
        Out:
            [comparative, superlative]
        """
        result = []
        
        for template in section.templates:
            if template.name == "en-adj":
                acount = self.get_positional_arg_count(template)

                comparative = None
                superlative = None

                if acount == 0:
                    pass
                    
                if acount == 1:
                    param1 = self.get_positional_arg(template, 0)
                    
                    if param1 == "er":
                        comparative  = label + "er"
                        superlative  = label + "est"
                        
                    elif param1 == "more":
                        comparative  = "more " + label
                        superlative  = "most " + label
                        
                    elif param1 == "further":
                        comparative  = "further " + label
                        superlative  = "furthest " + label
                        
                    elif param1 == "+":
                        comparative  = "further " + label
                        superlative  = None
                        
                    elif param1 == "-":
                        # not comparative
                        continue
                        
                    elif param1 == "?":
                        # unknown forms. skip
                        continue
                        
                    else:
                        comparative  = param1
                        
                        if label.endswith("er"):
                            superlative  = label[:-2] + "est"
                        else:
                            superlative  = label + "est"
        
                elif acount == 2:
                    param1 = self.get_positional_arg(template, 0)
                    param2 = self.get_positional_arg(template, 1)
                    comparative  = param1
                    superlative  = param2
                   
                # sup
                sup = self.get_named_arg(template, "sup")
                if sup and acount >= 1:
                    comparative  = self.get_positional_arg(template, 0)
                    superlative  = sup
                    
                sup2 = self.get_named_arg(template, "sup1")
                if sup2 and acount >= 2:
                    comparative  = self.get_positional_arg(template, 1)
                    superlative  = sup2
                    
                sup3 = self.get_named_arg(template, "sup2")
                if sup3 and acount >= 3:
                    comparative  = self.get_positional_arg(template, 2)
                    superlative  = sup3
                    
                sup4 = self.get_named_arg(template, "sup3")
                if sup4 and acount >= 4:
                    comparative  = self.get_positional_arg(template, 3)
                    superlative  = sup4

                result.append( comparative )
                result.append( superlative )
                
        return result
        
        
    def get_exp_from_template(self, text):
        # {{ux|en|I '''do''' not go there often.}}
        # {{quote-book|lang=en|passage=...}}

        parsed = wtp.parse(text)
        
        result = []
        
        for t in parsed.templates:
            # ux
            if t.name == "ux":
                if len(t.arguments) >= 2:
                    lang = self.get_positional_arg(t, 0)
                    s = self.get_positional_arg(t, 1)
                    result.append( (lang, s, t.string) )

            # quote-book
            elif t.name == "quote-book":
                passage = self.get_named_arg(t, "passage")
                lang = self.get_named_arg(t, "lang")
                
                result.append( (lang, passage, t.string) )
            
            # RQ:Birmingham Gossamer
            elif t.name == "RQ:Birmingham Gossamer":
                passage = self.get_named_arg(t, "passage")
                lang = self.get_named_arg(t, "lang")
                
                result.append( (lang, passage, t.string) )
            
            # quote-journal
            elif t.name == "quote-journal":
                passage = self.get_named_arg(t, "passage")
                lang = self.get_named_arg(t, "lang")
                
                result.append( (lang, passage, t.string) )
            
        return result
        
    def get_list_top_level(self, wlist, result):
        for i, l in enumerate(wlist.items):
            result.append( l )
            
    def get_li_recursive(self, wlist, result, level=0):
        for i, l in enumerate(wlist.items):
            result.append( (level, l) )
            
            for sub in wlist.sublists(i, pattern=":"):
                self.get_li_recursive(sub, result, level+1)
     
    def remove_tamplates(self, s):
        parsed = wtp.parse(s)
        cleaned = s
        
        for t in parsed.templates:
            cleaned = cleaned.replace(t.string, "")
        
        return cleaned
        

    def get_related(self, section):
        """
        In:
            section
            
        Out:
            [
                (lang, related),
                (lang, related),
                (lang, related)
            ]
        """
        # print(dir(t))
        # {{rel-top|related terms}}
        #   * {{l|en|knight}}
        #
        # {{rel-top|related terms}}
        # * {{l|en|knight}}
        
        
        #s = "{{rel-top|related terms}}"
        #lst = self.get_list_after_string(parsed, s)
        
        result = []
        
        found = False
        pos = 0
        
        for i, t in enumerate(section.templates):
            if t.name == "rel-top":
                if len(t.arguments) >= 1:
                    if t.arguments[0].value == "related terms":
                        found = True
                        pos = i

        if found:
            for t in section.templates[pos+1:]:
                # next templates with name 'l'
                if t.name == "l":
                    if len(t.arguments) >= 2:
                        lang = t.arguments[0].value
                        word = t.arguments[1].value                
                        result.append( (lang, word) )
                    
                else: 
                    break                    
                        
        return result

    def get_alternatives(self, section):
        """
        In:
            section
            
        Out:
            [
                (lang, alt),
                (lang, alt),
                (lang, alt)
            ]
        """
        # ==English== section here
        # ===Alternative forms===
        # * {{l|en|hower}} {{qualifier|obsolete}}
        
        result = []
        
        for sec in section.sections:
            title = sec.title.strip()
            
            if title == "Alternative forms":
                for t in sec.templates:
                    # * {{l|en|hower}} {{qualifier|obsolete}}
                    if t.name == "l":
                        if self.get_positional_arg_count(t) >= 2:
                            lang = self.get_positional_arg(t, 0)
                            term = self.get_positional_arg(t, 1)
                            result.append( (lang, term) )
                
        return result
        
        
    def setup_word(self, word, 
        label, lang, lang2, lang_title, type, 
        explainations,
        is_male_variant, is_female_variant,
        male_variant, female_variant,
        is_single_variant, is_plural_variant,
        single_variant, plural_variant,
        alternatives,
        related,
        is_verb_past, is_verb_present, is_verb_futur,
        conjugations,
        synonyms,
        translations
        ):
        
        word.LabelName = label
        word.LanguageCode = lang
        word.Type = type
        word.ExplainationExample = explainations
        word.IsMaleVariant = is_male_variant
        word.IsFemaleVariant = is_female_variant
        word.MaleVariant = male_variant
        word.FemaleVariant = female_variant
        word.IsSingleVariant = is_single_variant
        word.IsPluralVariant = is_plural_variant
        word.SingleVariant = single_variant
        word.PluralVariant = plural_variant
        word.AlternativeFormsOther = alternatives
        word.RelatedTerms = related
        word.IsVerbPast = is_verb_past
        word.IsVerbPresent = is_verb_present
        word.IsVerbFutur = is_verb_futur
        word.Conjugation = conjugations
        word.Synonyms = synonyms
        
        for (tr_lang, tr_string, tr_male_female) in translations:
            if tr_lang == "en":
                word.Translation_EN.append(tr_string)            
            elif tr_lang == "fr":
                word.Translation_FR.append(tr_string)
            elif tr_lang == "de":
                word.Translation_DE.append(tr_string)
            elif tr_lang == "es":
                word.Translation_ES.append(tr_string)
            elif tr_lang == "ru":
                word.Translation_RU.append(tr_string)
            elif tr_lang == "cn":
                word.Translation_CN.append(tr_string)
            elif tr_lang == "pt":
                word.Translation_PT.append(tr_string)
            elif tr_lang == "ja":
                word.Translation_JA.append(tr_string)
                
        # unique
        word.Translation_EN = unique(word.Translation_EN)
        word.Translation_FR = unique(word.Translation_FR)
        word.Translation_DE = unique(word.Translation_DE)
        word.Translation_ES = unique(word.Translation_ES)
        word.Translation_RU = unique(word.Translation_RU)
        word.Translation_CN = unique(word.Translation_CN)
        word.Translation_PT = unique(word.Translation_PT)
        word.Translation_JA = unique(word.Translation_JA)


def print_list(title, lst):
    """
    Print title and indented list. For debugging.
    """
    print(title)
    
    if lst:
        for e in lst:
            print("  ", e)    
    else:
        print("[]")

def pprint(word):
    """
    Print Word human readable.
    """
    print(word.LabelName)
    
    for k in dir(word):
        if k[0] != "_":
            if k != "LabelName":
                print("  ", k.ljust(22) + ":", getattr(word, k))

def get_all_sections():
    """
    Debugging tool for extraction all section names from dump.
    """
    lang = "en"
    cache_folder = "en"
    create_storage(cache_folder)
    local_file = os.path.join(cache_folder, lang+"wiktionary-latest-pages-articles.xml.bz2")
    
    wd = Wikidict()
    wd.set_limit(1000)
    sections = wd.get_all_dump_sections(local_file)
    
    for section in sections:
        print(section)


### Tests ###
class TestStringMethods(unittest.TestCase):
    """
    Main test class for unit tests.
    """
    def __init__(self, *args, **kwargs):
        create_storage(TXT_FOLDER)
        create_storage(LOGS_FOLDER)
        super().__init__(*args, **kwargs)
        
    @unittest.skip("skip")
    def test_a(self):
        text = "# 1\n## 2\n## 3"
        print( [x for x in list_tokenizer(text) ] )
        print( [x for x in list_generator(text) ] )

        print( "list_heirarhy:" )
        for a in list_generator( text ): 
            dump_list( list_heirarhy(a) )
            
        exit(0)

        t = TemplateParser()
        #found = find_first("abc {{tpl|{{tpl2}}}} def", ['{{', '}}'])
        #print(found)
        p = t.parse("abc")
        p = t.parse("{{tpl|1|b|c|d=2}}")
        p = t.parse("{{tpl|1|b|c|d=2}} {{a|{{z}}}}")
        #p = t.parse("abc {{tpl}} def")
        #p = t.parse("abc {{1}} x {{2}} def")
        #p = t.parse("abc {{ {{1}} x {{2}} }} def")
        #p = t.parse("abc {{{{1}} x {{2}}}} def")
        print(p)
        print([x.arguments for x in p if isinstance(x, Template)])
        print([x.named_arguments for x in p if isinstance(x, Template)])
        print([x.positional_arguments for x in p if isinstance(x, Template)])
        print([x.templates for x in p if isinstance(x, Template)])
        exit(0)

    @unittest.skip("skip")
    def test_read_bz2(self):
        return
        filename = "./ru/ruwiktionary-latest-pages-articles.xml.bz2"
        source_file = bz2.BZ2File(filename, "r")
        self.assertTrue(source_file)

        count = 0
        for line in source_file:
            count += 1
            if count > 3:
               break
        source_file.close()

        self.assertTrue(count > 3)

    @unittest.skip("skip")
    def test_parse_xml(self):
        xml = get_contents("./test/page.xml")

        import io
        stream = io.BytesIO(bytearray(xml, 'UTF-8'))
        
        self.found = None
        
        def page_callback(label, text):
            self.assertTrue(label)
            self.assertTrue(text)
            self.found = True

        parser = XMLParser()
        parser.parse(stream, page_callback)
        
        self.assertTrue(self.found is not None)

    #@unittest.skip("skip")
    def test_get_related(self):
        text = get_contents("./test/horse.txt")
        
        text_parser = TextParser()
        
        parsed = wtp.parse(text)
        
        related = text_parser.get_related(parsed)        
        related = text_parser.filter_allowed_langs(related)
        
        #print_list("related:", related)
        
        self.assertTrue(len(related) == 14)

    #@unittest.skip("skip")
    def test_get_types(self):
        text = get_contents("./test/horse.txt")

        text_parser = TextParser()
        
        label = "horse"
        
        parsed = wtp.parse(text)
        
        types = []
        
        for section in parsed.sections:
            if section.title.strip() == "English":
                types = text_parser.get_types(section)
                break # only fisrt
    
        self.assertTrue(len(types) == 3)
        
        for section in parsed.sections:
            if section.title.strip() == "Middle English":
                types = text_parser.get_types(section)
                break # only fisrt
    
        self.assertTrue(len(types) == 2)
        
    #@unittest.skip("skip")
    def test_get_explainations(self):
        text = get_contents("./test/horse.txt")

        text_parser = TextParser()
        
        label = "horse"
        
        explainations = []
        
        parsed = wtp.parse(text)
        for section in parsed.sections:
            if section.level == 2 and section.title.strip() == "English":
            
                for sec in section.sections:
                    if sec.level == 4 and sec.title.strip() == "Noun":                    
                    
                        #print(sec.title)
                        explainations += text_parser.get_explainations(sec)    
                        #print_list("explainations:", explainations)

        self.assertTrue(len(explainations) == 9)

        #
        explainations = []

        for section in parsed.sections:
            if section.level == 2 and section.title.strip() == "English":
            
                for sec in section.sections:
                    if sec.level == 4 and sec.title.strip() == "Verb":    
                
                        #print(sec.title)
                        explainations += text_parser.get_explainations(sec)    
                        #print_list("explainations:", explainations)
        
        self.assertTrue(len(explainations) == 7)
        
    #@unittest.skip("skip")
    def test_get_synonyms(self):
        text = get_contents("./test/horse.txt")

        text_parser = TextParser()
        
        label = "horse"
        synonyms = []
        
        parsed = wtp.parse(text)
        for section in parsed.sections:
            if section.level == 2 and section.title.strip() == "English":
            
                for sec in section.sections:
                    if sec.level == 4 and sec.title.strip() == "Noun":
                    
                        #print(sec.title)
                        synonyms += text_parser.get_synonyms(sec)
                        #synonyms = text_parser.filter_allowed_langs(synonyms)
                        #print_list("synonyms:", synonyms)
                        
        self.assertTrue(len(synonyms) == 12)
                        
        synonyms = []
        for section in parsed.sections:
            if section.level == 2 and section.title.strip() == "English":
            
                for sec in section.sections:
                    if sec.level == 4 and sec.title.strip() == "Verb":
                    
                        #print(sec.title)
                        synonyms = text_parser.get_synonyms(sec)    
                        #synonyms = text_parser.filter_allowed_langs(synonyms)
                        #print_list("synonyms:", synonyms)

        self.assertTrue(len(synonyms) == 0)
                
    #@unittest.skip("skip")
    def test_get_translations(self):
        text = get_contents("./test/horse.txt")

        text_parser = TextParser()
        
        label = "horse"
        
        parsed = wtp.parse(text)
        
        translations = []
        
        for section in parsed.sections:
            if section.level == 2 and section.title.strip() == "English":
            
                for sec in section.sections:
                    if sec.level == 4 and sec.title.strip() == "Noun":                    
                        print(sec.title)
                        translations += text_parser.get_translations(sec)    
                        translations = text_parser.filter_allowed_langs(translations)
                        #print_list("translations:", translations)

        self.assertTrue(len(translations) == 59)
         
         
        translations = []

        for section in parsed.sections:
            if section.level == 2 and section.title.strip() == "English":
            
                for sec in section.sections:
                    if sec.level == 4 and sec.title.strip() == "Verb":                    
                    
                        #print(sec.title)
                        translations += text_parser.get_translations(sec)
                        translations = text_parser.filter_allowed_langs(translations)
                        #print_list("translations:", translations)

        self.assertTrue(len(translations) == 0)
        
    #@unittest.skip("skip")
    def test_get_conjugations(self):
        text = get_contents("./test/do.txt")

        text_parser = TextParser()
        
        label = "do"
        
        parsed = wtp.parse(text)
        
        conjugations = []
        
        for section in parsed.sections:
            if section.level == 2 and section.title.strip() == "English":
            
                for sec in section.sections:
                    if sec.level == 4 and sec.title.strip() == "Verb":                    
                    
                        #print(sec.title)
                        conjugations = text_parser.get_conjugations(sec, label)
                        #print_list("conjugations:", conjugations)

        self.assertTrue(len(conjugations) == 5)
        self.assertTrue(conjugations == ['do', 'did', 'done', 'doing', 'does'])
        
    #@unittest.skip("skip")
    def test_get_is_plural(self):
        text = get_contents("./test/cats.txt")
        #text = get_contents("./test/horses.txt")

        text_parser = TextParser()
        
        label = "cats"
        
        parsed = wtp.parse(text)
        
        is_plural = []
        
        for section in parsed.sections:
            if section.level == 2 and section.title.strip() == "English":    
                #print(sec.title)
                is_plural = text_parser.get_is_plural(section)
                #print_list("is_plural:", is_plural)        
                        
        self.assertTrue(len(is_plural) == 2)
        self.assertTrue(is_plural == [('en', True), ('en', True)])
        
    #@unittest.skip("skip")
    def test_parse_list(self):
        s = """# a
#* aa1
#*: aaa1
"""
        
        lines = s.split("\n")        
        text_parser = TextParser()        
        result = text_parser.parse_list(lines)        
        self.assertTrue(result == [['# a', ['#* aa1', ['#*: aaa1']]]])
        
        # bugged
        s = """## a
##* aa1
##*: aaa1
"""
        
        lines = s.split("\n")        
        text_parser = TextParser()        
        result = text_parser.parse_list(lines)        
        self.assertTrue(result == [['## a', ['##* aa1', ['##*: aaa1']]]])
        
    @unittest.skip("skip")
    def test_get_get_skip_spaces(self):
        text = "   abc"
        text = "abc"
        text = ""
        print( skip_spaces(text, pos=0) )
        exit(0)
        
    @unittest.skip("skip")
    def test_get_get_get_title(self):
        text = "== Title =="
        print( get_title(text) )
        (level, title, endpos) = get_title(text)
        print( text[endpos:] )
        exit(0)

    #@unittest.skip("skip")
    def test_get_get_sentences(self):
        text = get_contents("./test/good.txt")
        label = "good"

        #print( [x for x in list_tokenizer(text) ] )
        #print( [x for x in list_generator(text) ] )

        print( "list_heirarhy:" )
        for a in list_generator( text ): 
            dump_list( list_heirarhy(a) )

        
    @unittest.skip("skip")
    def test_get_is_male_variant(self):
        return
        text = get_contents("./test/cat.txt")

        text_parser = TextParser()
        
        label = "cat"
        
        parsed = wtp.parse(text)
        
        for section in parsed.sections:
            if section.level == 2 and section.title.strip() == "English":
            
                for sec in section.sections:
                    if sec.level == 3 and sec.title.strip() == "Etymology 1":
                    
                        print(sec.title)
                        is_male = text_parser.get_is_male_variant(sec)
                        print_list("is_male:", is_male)
                        
    @unittest.skip("skip")
    def test_4_load_dump_from_http(self):
        return
        lang = "en"

        remote_file = "https://dumps.wikimedia.org/"+lang+"wiktionary/latest/"+lang+"wiktionary-latest-pages-articles.xml.bz2"

        cache_folder = "cached"
        create_storage(cache_folder)
        local_file = os.path.join(cache_folder, lang+"wiktionary-latest-pages-articles.xml.bz2")

        #
        import requests
        import shutil
                
        r = requests.get(remote_file, auth=('usrname', 'password'), verify=False,stream=True)
        r.raw.decode_content = True
        
        with open(local_file, 'wb') as f:
            shutil.copyfileobj(r.raw, f)  
                
    @unittest.skip("skip")
    def test_5_load_into_memory(self):
        return
        lang = "en"
        
        cache_folder = "cached"
        create_storage(cache_folder)
        local_file = os.path.join(cache_folder, lang+"wiktionary-latest-pages-articles.xml.bz2")

        # parse
        wd = Wikidict()
        wd.set_limit(1000)
        wd.parse_dump(local_file)
        
        # save to json
        save_to_json(wd.treemap, 'test/result.json')
    
    #@unittest.skip("skip")
    def test_6_export_to_json(self):
        text_parser = TextParser()
        
        label = "horse"
        text = get_contents("./test/horse.txt")
        
        # treemap
        treemap = sorteddict()
        treemap[label] = text_parser.parse(label, text)
        
        # save to json
        save_to_json(treemap, 'test/test.json')
    
    #@unittest.skip("skip")
    def test_7_load_from_json(self):
        treemap = load_from_json('test/test.json')

        self.assertTrue('horse' in treemap)
        self.assertTrue(len([ w for w in treemap['horse'] if isinstance(w, Word) ]) == 16)
        self.assertTrue(all([ w.LabelName == 'horse' for w in treemap['horse'] if isinstance(w, Word) ]))
    
    #@unittest.skip("skip")
    def test_8_save_to_disk(self):
        text_parser = TextParser()
        
        label = "horse"
        text = get_contents("./test/horse.txt")
        
        # treemap
        treemap = sorteddict()
        treemap[label] = text_parser.parse(label, text)

        # save to pickle
        pickle_file = "test/data.pickled"
        save_to_pickle(treemap, pickle_file)
        
    #@unittest.skip("skip")
    def test_9_load_from_disk(self):
        pickle_file = "test/data.pickled"
        treemap = load_from_pickle(pickle_file)        

        self.assertTrue('horse' in treemap)
        self.assertTrue(len([ w for w in treemap['horse'] if isinstance(w, Word) ]) == 16)
        self.assertTrue(all([ w.LabelName == 'horse' for w in treemap['horse'] if isinstance(w, Word) ]))
    
    @unittest.skip("skip")
    def test_text_parser(self):
        # 1) Wiktionary Loader from dump : download the file source with HTTP (This module have one parameter : Language code)
        # 2) Load into memory (TreeMap): parse the source file 
        # 3) Export to 9 text file JSON UTF-8
        # 4) Load from JSON text file into TreeMap
        # 5) Save to disk (Pickle)
        # 6) Load from disk (Pickle)
        pass
        
    #@unittest.skip("skip")
    def test_parse_text(self):
        label = "hour"
        label = "homeworld"
        label = "chat"

        text = get_contents("./test/" + label + ".txt")

        # parse
        text_parser = TextParser()
        words = text_parser.parse(label, text)
        
        self.assertTrue(len(words) == 14)
        
        # save to json
        #save_to_json(words, "test/" + sanitize_filename(label) + ".json",)
        
    #@unittest.skip("skip")
    def test_main_1000(self):
        # download
        wd = Wikidict()
        local_file = wd.download("en", use_cached=True)
        
        # parse
        wd.set_limit(1000)
        wd.parse_dump(local_file)
        
        # save to json
        save_to_json(wd.treemap, 'test/result.json')
          

def test():
    """
    Run all tests.
    """
    unittest.main()


def one_file(label = "cat"):
    """
    Parse only on word 'label'. (For Debugging)
    
    Get text from the test/<label>.txt
    Save to the test/<label>.json
    """
    log.info("Word: %s", label)
    src_file = "./test/" + label + ".txt"
    log.info("Loading from: %s", src_file)
    text = get_contents(src_file)

    # parse
    log.info("Parsing")
    text_parser = TextParser()
    words = text_parser.parse(label, text)
    
    # pack
    treemap = sorteddict()
    treemap[label] = words
    
    # save to json
    json_file = os.path.join(TEST_FOLDER, sanitize_filename(label) + ".json")
    log.info("Saving to: %s", json_file)
    save_to_json(treemap, json_file)

    log.info("Status: words:%d, labels:%s", len(words), str([w.LabelName for w in words]))
    log.info("Done!")
        

### Main ###    
def main():
    """
    Run parser.
    Parse, save to json.
    """
    create_storage(TXT_FOLDER)

    # download
    wd = Wikidict()
    local_file = wd.download("en", use_cached=True)
    
    # parse
    #wd.is_need_save_txt = True
    #wd.set_limit(100000)
    wd.parse_dump(local_file)
    
    # save to json
    create_storage("test")
    #save_to_json(wd.treemap, os.path.join(TEST_FOLDER, 'result.json'))

    # save to pickle
    pickle_file = os.path.join(TEST_FOLDER, "data.pickled")
    #save_to_pickle(wd.treemap, pickle_file)


# setup loggers
create_storage(LOGS_FOLDER)
logging.basicConfig(level=log_level)
log             = setup_logger('main', format='%(levelname)s: %(message)s')
log_non_english = setup_logger('log_non_english')
log_unsupported = setup_logger('log_unsupported')


if __name__ == "__main__":
    #test()
    main()
    #one_file("cat")
    
