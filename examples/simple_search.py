import pyanimecli as pac

# Simple search example
results = pac.search("Dragon ball")
for anime in results:
    print(f"{anime['title']} ({anime['id']}) - Type: {anime['type']}")