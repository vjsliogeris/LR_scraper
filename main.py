
from pathlib import Path

from lrscraper import scraper

results_dir = Path('results/')

scraper.scrape(results_dir)
