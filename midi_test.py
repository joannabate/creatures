import mido

inport = mido.open_input()

for msg in inport:
    print(msg)