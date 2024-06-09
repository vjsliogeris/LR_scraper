
from pathlib import Path
import argparse

from lrscraper import scraper

def main(args):
    results_dir = Path(args.output)
    scraper.scrape(results_dir)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                    prog=Path(__file__).name,
                    description='Scraper the official parliament website for speeches',
                    epilog='Vytenis :)')
    parser.add_argument(
            '-o', '--output',
            default='results',
            help='Target directory for the speeches to be saved to.')
    args = parser.parse_args()
    main(args)
