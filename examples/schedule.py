import pyanimecli as pac

# Get airing schedule for today
from datetime import date
pac.schedule(date.today().isoformat(), pretty_print=True)