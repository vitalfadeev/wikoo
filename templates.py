def en_conj(t, label):
    """
    {{en-conj|basic form|simple past form|past participle|present participle|simple present third-person form}} 
    
    {{en-conj|listen}}
    {{en-conj|lov|e}}
    {{en-conj|cr|y}}
    {{en-conj|trave|l}}
    {{en-conj|cat|ch}}
    {{en-conj|take|took|taken|taking}}
    
    Out:
        [ basic, simple_past, past_participle, present_participle, simple_present_third_person ]
    """
    result = []
    
    acount = len(t.args)
    
    if acount == 1:
        pass
        
    elif acount == 2:
        param1 = t.arg(0)
        param2 = t.arg(1)
        
        if param2 == "e":
            result.append( param1+param2 )
            result.append( param1+"ed" )
            result.append( param1+"en" )
            result.append( param1+"ing" )
            result.append( param1+"es" )

        elif param2 == "y":
            result.append( param1+param2 )
            result.append( param1+"ed" )
            result.append( param1+"en" )
            result.append( param1+"ing" )
            result.append( param1+"es" )

        elif param2 == "l":
            result.append( param1+param2 )
            result.append( param1+"ed" )
            result.append( param1+"en" )
            result.append( param1+"ing" )
            result.append( param1+"es" )

        elif param2 == "ch":
            result.append( param1+param2 )
            result.append( param1+"ed" )
            result.append( param1+"en" )
            result.append( param1+"ing" )
            result.append( param1+"es" )
            
    else:
        for k,a in t.args.items():
            result.append( a.as_string() )
    
    return result

def ang_noun(t, label):
    # head  - alt term
    # 1     - f | m
    # 2     - plural form
    # pl2   - second plural
    
    head = t.arg(0)
    p1   = t.arg(1)
    p2   = t.arg("head")
    pl2  = t.arg("pl2")
    
    return (head, p1, p2, pl2)
    
def en_noun(t, label):
    """
    {{en-noun}}
    {{en-noun|es}}
    {{en-noun|...}}
    {{en-noun|...|...}}
    
    out: (single, [plural], is_uncountable)
    """
    s = label
    p = []
    is_uncountable = False
    
    # http://en.wiktionary.org/wiki/Template:en-noun
    head = t.arg("head", label)
    p1 = t.arg(0)
    p2 = t.arg(1)
    
    if p1 == "-":
        # uncountable
        is_uncountable = True
        
        if p2 == "s":
            # ends by s
            p.append(head + "s")
            
        elif p2 is not None:
            # word
            p.append(p2)
    
    elif p1 == "es":
        # add es
        p.append(head + "es")
        
    elif p1 is not None:
        # use term
        p.append(p1)
        
    elif p1 is None and p2 is None:
        p.append(head+"s")

    for k,a in t.args.items():
        if not a.is_named():
            if k == 0 or k == 1:
                continue
            
            p.append(a.as_string())
                    
    return (s, p, is_uncountable)

def en_verb(t, label):
    """
    Out:
        (label_third, label_present_participle, label_simple_past, label_past_participle)
    """
    # ====Verb==== here
    
    label_third              = None
    label_present_participle = None
    label_simple_past        = None
    label_past_participle    = None
    
    # http://en.wiktionary.org/wiki/Template:en-verb
    acount = t.get_positional_args_count()

    if acount == 0:
        label_third              = label + "s"
        label_present_participle = label + "ing"
        label_simple_past        = label + "ed"
        label_past_participle    = label + "ed"
    elif acount == 1:
        param1 = t.arg(0)
        if "d" == param1:
            label_third              = label + "s"
            label_present_participle = label + "ing"
            label_simple_past        = label + "d"
            label_past_participle    = label + "d"
        elif "es" == param1:
            label_third              = label + "es"
            label_present_participle = label + "ing"
            label_simple_past        = label + "ed"
            label_past_participle    = label + "ed"
        else:
            label_third              = label  + "s"
            label_present_participle = param1 + "ing"
            label_simple_past        = param1 + "ed"
            label_past_participle    = param1 + "ed"
        
    elif acount == 2:
        param1 = t.arg(0)
        param2 = t.arg(1)
        if "es" == param2:
            label_third              = param1 + "es"
            label_present_participle = param1 + "ing"
            label_simple_past        = param1 + "ed"
            label_past_participle    = param1 + "ed"
        elif "ies" == param2:
            label_third              = param1 + "ies"
            label_present_participle = label + "ing"
            label_simple_past        = param1 + "ied"
            label_past_participle    = param1+ "ied"
        elif "d" == param2:
            label_third              = param1 + "s"
            label_present_participle = param1 + "ing"
            label_simple_past        = param1 + "d"
            label_past_participle    = param1 + "d"
        elif "ing" == param2:
            label_third              = label  + "s"
            label_present_participle = param1 + "ing"
            label_simple_past        = label  + "d"
            label_past_participle    = label  + "d"
            
    elif acount == 3:
        param1 = t.arg(0)
        param2 = t.arg(1)
        param3 = t.arg(2)
        if "es" == param3:
            label_third              = param1 + param2 + "es"
            label_present_participle = param1 + param2 + "ing"
            label_simple_past        = param1 + param2 + "ed"
            label_past_participle    = param1 + param2 + "ed"
        elif "ed" == param3 and "i" == param2:
            label_third              = param1 + param2 + "es"
            label_present_participle =label + "ing"
            label_simple_past        = param1 + param2 + "ed"
            label_past_participle    = param1 + param2 + "ed"
        elif "ed" == param3:
            label_third              = label + "s"
            label_present_participle = param1 + param2 + "ing"
            label_simple_past        = param1 + param2 + "ed"
            label_past_participle    = param1 + param2 + "ed"
        elif "ing" == param3:
            label_third              = label + "s"
            label_present_participle = param1 + param2 + "ing"
            label_simple_past        = label + "d"
            label_past_participle    = label + "d"
        else:
            if not param1:
                label_third = label + "s"
            else:
                label_third = param1
            label_present_participle = param2
            label_simple_past        = param3
            label_past_participle    = param3
        
    elif acount == 4:
        param1 = t.arg(0)
        param2 = t.arg(1)
        param3 = t.arg(2)
        param4 = t.arg(3)
        label_third              = param1
        label_present_participle = param2
        label_simple_past        = param3
        label_past_participle    = param4
    
    for key, a in t.args.items():
        if isinstance(key, str):
            if key.startswith("pres"):
                label_present_participle = a.as_string()
            elif key == "past2":
                if acount == 3:
                    label_simple_past = a.as_string()
                    label_past_participle = a.as_string()
                else:
                    label_simple_past = a.as_string()
                
    return (label_third, label_present_participle, label_simple_past, label_past_participle)

def plural_of(t, label):
    """
    out: (lang, single, showntext)
    """
    # {{plural of|<langcode>|<primary entry goes here>}}
    # {{plural of|cat|lang=en}}
    # https://en.wiktionary.org/wiki/Template:plural_of
    
    lang = t.arg("lang")
    p1 = t.arg(0)
    p2 = t.arg(1)
    p3 = t.arg(2)
    p4 = t.arg(3)
    t = t.arg("t")
    tr = t.arg("tr")
    ts = t.arg("ts")
    sc = t.arg("sc")
    id = t.arg("id")

    lang = lang if lang is not None else p1
    single = p2
    showntext = p3 if p3 is not None else p2
    
    return (lang, single, showntext)

def present_participle_of(t, label):
    """
    out: (lang, present, showntext)
    """
    # {{present participle of|cat|lang=en|nocat=1}}
    lang = t.arg("lang")
    p1 = t.arg(0)
    p2 = t.arg(1)
    p3 = t.arg(2)
    p4 = t.arg(3)
    t = t.arg("t")
    tr = t.arg("tr")
    ts = t.arg("ts")
    sc = t.arg("sc")
    id = t.arg("id")

    lang = lang if lang is not None else p1
    present = p2
    showntext = p3 if p3 is not None else p2
    
    return (lang, present, showntext)

def head(t, label):
    # {{head|en|verb form}}
    pass
