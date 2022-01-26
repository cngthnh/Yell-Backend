import random

def generateCode():
    code = ''
    for i in range(0, 4):
        code += str(random.randint(0, 9))
    return code