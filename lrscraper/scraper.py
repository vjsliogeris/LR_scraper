
from pathlib import Path
import hashlib
import logging
import os
import re
import requests

from tqdm import tqdm

results_dir = Path('results/')

def get_anchor_href(text: str) -> str:
    href_pattern = r'href="([\w\.\?\=\-\:\/]+)"'
    match = re.findall(href_pattern, text)
    return match[0]


def split_cadences(response_text):
    header_pattern = r'<tr><td colspan="3" class="ctb">&nbsp;<b>\d\d\d\d - \d\d\d\d met. kadencija<\/b>&nbsp;<\/td><\/tr>'
    sessions = []
    session_headers = list(re.finditer(header_pattern, response_text))
    for i, match in enumerate(session_headers):
        title_tag = match.group()
        title_regex = r'<b>(.+)</b>'
        title = re.findall(title_regex, title_tag)[0]
        start_index = match.span()[1]

        if i < len(session_headers)-1:
            end_index = session_headers[i+1].span()[0]-1
        else:
            end_index = len(response_text)-1
        sessions.append((title, start_index, end_index))
    return sessions


def scrape(include_emergencies: bool = False):
    logging.basicConfig(filename = 'dump.log', encoding='utf-8', level=logging.DEBUG)
    # THIS ID APPROACH IS TRASH THEY DO NOT KEEP DATA LIKE NON RETARDS GOTTA SCRAPE THE HTML

    sittings_url_base = 'https://www3.lrs.lt/pls/inter/'
    sessions_url = sittings_url_base + 'w5_sale.kad_ses'
    sessions_response = requests.get(sessions_url)
    response_text = sessions_response.text
    sessions = split_cadences(response_text)
    for title, start_index, end_index in (pbar:=tqdm(sessions)):
        pbar.set_description(f"Processing {title}")
        relevant_text = response_text[start_index : end_index]
        title = title.replace(' ','_')
        save_dir = results_dir / Path(title)
        save_dir.mkdir(parents=True, exist_ok = True)
        scrape_section(relevant_text, save_dir)


def scrape_section(text, save_dir: Path):
    # THIS ID APPROACH IS TRASH THEY DO NOT KEEP DATA LIKE NON RETARDS GOTTA SCRAPE THE HTML

    file_url_base = 'https://e-seimas.lrs.lt'
    sittings_url_base = 'https://www3.lrs.lt/pls/inter/'
    pattern_reg_sess = r'<td class="ltb">&nbsp;<a href="[\w\.?\=]+">\d+ eilinë sesija<\/a>&nbsp;<\/td>'
    session_lines = re.findall(pattern_reg_sess, text)
    for s_line in session_lines:
        session_regex = r'\d+ \w+. \w+'
        logging.debug(f'Regexing {s_line} with {session_regex}')
        session_desc = re.search(session_regex, s_line).group()
        href = get_anchor_href(s_line)
        full_session_url = sittings_url_base + href
        session_response = requests.get(full_session_url)
        session_text = session_response.text
        morning_evening_pattern = r'<a href="w5_sale\.fakt_pos\?p_fakt_pos_id=-\d+">(?:rytinis|vakarinis)</a>'
        logging.debug(f'Regexing {full_session_url} with {morning_evening_pattern}')
        morning_evening_urls = re.findall(morning_evening_pattern, session_text)
        for morning_evening_url in morning_evening_urls:
            href = get_anchor_href(morning_evening_url)
            sitting_url = sittings_url_base + href
            sitting_response = requests.get(sitting_url)
            sitting_text = sitting_response.text
            stenogram_pattern = r'<a href=".+" target="_new">Stenograma<\/a>'
            logging.debug(f'Regexing {sitting_url} with {stenogram_pattern}')
            stenogram_match = re.search(stenogram_pattern, sitting_text) 
            if not stenogram_match:
                logging.warning('Could not find pattern!')
                continue
            stenogram_tag = stenogram_match.group()
            stenogram_url = get_anchor_href(stenogram_tag)
            stenogram_site_response = requests.get(stenogram_url)
            stenogram_site_text = stenogram_site_response.text
            file_tag_pattern = r'<a href="\/[(?:\w\.)\/]+"><img id="[\w\:]+" src="/resources/img/docx\.png\?pfdrid_c=true" alt="" /></a>'
            logging.debug(f'Regexing {stenogram_url} with {file_tag_pattern}')
            file_match = re.search(file_tag_pattern, stenogram_site_text)
            if not file_match:
                logging.warning('Could not find pattern!')
                continue
            file_tag = file_match.group()
            file_url = file_url_base + get_anchor_href(file_tag)
            file_response = requests.get(file_url)
            file_content = file_response.content
            filename = hashlib.md5(file_content).digest().hex()
            with open(save_dir / Path(filename+".docx"), "wb") as binary_file:
                binary_file.write(file_content)
