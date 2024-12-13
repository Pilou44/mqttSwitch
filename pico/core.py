from machine import unique_id

def getId():
    id = unique_id()
    stringId = ""
    for b in id:
        stringId += hex(b)[2:]
    return stringId
