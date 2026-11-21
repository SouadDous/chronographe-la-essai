"""Lance Chrome (installé) ou, à défaut, le Chromium fourni par Playwright."""
async def lancer(p):
    try: return await p.chromium.launch(channel='chrome')
    except Exception: return await p.chromium.launch()
