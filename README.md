# wikoo
Wikitionary data parser and extractor

## Usage ##
    import wikoo
    root = wikoo.parse(text)
  
result:

    <Section>
  
### Example ###

    text = """
    ==English== 
    
    ===Verb===
    {{noun}}
    
    # {{expl1}}
    # {{expl2}}
    ## expl2-1
    # expl3 {{tpl|aaa {{sub}} }} {{second|1|2|3}} tail
    """
    
    root = wikoo.parse(text)
    
    dump_section(root)
    
