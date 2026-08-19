from app.crawler import KeelungSightsCrawler

crawler = KeelungSightsCrawler()
sights = crawler.get_items("七堵")

for sight in sights:
    print(sight)
