import pyanimecli as pac

# Get recent episodes
recent = pac.recent_episodes()
for ep in recent:
    print(ep)