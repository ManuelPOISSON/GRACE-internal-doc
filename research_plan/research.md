
# Q1

How to improve auto pentest?
    Does using MAL improve auto pentest?

Goal: MAL must help the attack agent to choose which action to do next

## Evaluation
- try auto pentest (requires trying environment (see bellow)):
a) without MAL
b) with MAL
Compare results

- define what is a good pentest
    a) more vulnerability discovered?
    b) stealthier?
    c) faster?
    d) less token consumed?

Training environment choice
- cyber-range
- ctf events
- bug bounty


# Q2

## Can we auto generate MAL language?

we need input to generate the language:
    What input?
        - attack traces
            - commands launched
            - pentest reports
            - ctf/bug bounty write up
        - defense logs
        - incident reponse report


    How to get these input?
        - publicly available
            - research dataset
            -  gitub/gitlab (writeup)
            -  blog post
        - only accessible by us
            - reports from Nordsnipe
        - we generate our traces
            - How
                - manually
                - using an llm (warning during evaluation. No evaluation on training data)
            - Were (see training environment)
        

### How to evaluate generated language?
lvl1: compiling: correct syntax?
lvl2: is it good at what it is supposed to to?
        What is it supposed to do?


