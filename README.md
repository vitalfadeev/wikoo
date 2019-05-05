# wikoo
Wiki article parser. 

* on input: text
* on output: Object tree

## Usage ##
    import wikoo
    root = wikoo.parse(text)
  
result:

    <Section>
        <Section>
            <Text>
            <Template?
            <Text>
        <Section>
            <Template?
            <LI>
            <LI>
            <LI>
            <Template?
  
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
    
