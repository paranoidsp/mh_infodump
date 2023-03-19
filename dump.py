# Get all PMQs about mental health

import requests as r
import lxml.html as lh
from typing import Dict

URL = "https://loksabha.nic.in/Questions/Qtextsearch.aspx"
TABLE_XPATH = '//*[@id="ContentPlaceHolder1_tblMember"]/tr/td/table'


def get_pmqs():
    """
    Get PMQs about mental health
    """
    # TODO handle case where results are not sorted by date by default
    # currently assumes that resuts will be sorted by date, latest first
    # so only reading questions till the last checked

    # Plan
    # Search for mental health questions
    # Get table, Q.NO and date
    # If already read, break and stop here
    # If not already read, download the english pdf, put it in folder if it
    # does not already exist
    # If folder already exists, delete
    # Paginate
    # Update csv

    # Get the viewstate token
    resp = r.get(URL)
    parsed_resp = lh.fromstring(resp.text)

    data = {
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": parsed_resp.get_element_by_id("__VIEWSTATE").value,
        "__VIEWSTATEGENERATOR": parsed_resp.get_element_by_id(
            "__VIEWSTATEGENERATOR"
        ).value,
        "__VIEWSTATEENCRYPTED": "",
        "__EVENTVALIDATION": parsed_resp.get_element_by_id("__EVENTVALIDATION").value,
        "ctl00$txtSearchGlobal": "",
        "ctl00$ContentPlaceHolder1$ddlfile": ".pdf",
        "ctl00$ContentPlaceHolder1$TextBox1": "mental health",
        "ctl00$ContentPlaceHolder1$searchbtn": "search",
        "ctl00$ContentPlaceHolder1$btn": "allwordbtn",
        "ctl00$ContentPlaceHolder1$btn1": "titlebtn",
        "ctl00$ContentPlaceHolder1$txtpage": "1",
    }

    # search page 1
    search_resp = r.post(URL, data)
    parsed_search = lh.fromstring(search_resp.text)

    # Get total number of pages
    num_pages = get_num_pages(parsed_search)
    print(f"Found {num_pages} pages of results, fetching them all...")

    # get headers
    headers = get_headers(parsed_search)

    total = 0

    results = []

    # paginate through them, get first row again just because I'm lazy
    for page in range(1, num_pages + 1):
        rows = get_results_from_page(data, page)
        print(f"=> Found {len(rows)} results from page {page}")
        total += len(rows)
        results.extend(rows)

    print("----------------------------------")
    print(f"Found a total of {len(results)} results!")


def get_headers(page: lh.HtmlElement):
    # using xpath for now
    table = page.xpath(TABLE_XPATH)[0]
    headers = [td.text.strip() for td in table.xpath("thead/tr/td")]

    return headers


def get_results_from_page(data: Dict[str, str], page: int):
    # set page number
    data["ctl00$ContentPlaceHolder1$txtpage"] = str(page)

    # fetch and parse
    search_resp = r.post(URL, data)

    return parse_page(lh.fromstring(search_resp.text))


def parse_page(page: lh.HtmlElement):
    # using xpath for now
    table = page.xpath(TABLE_XPATH)[0]

    return table.xpath("tr")


def get_num_pages(page: lh.HtmlElement) -> int:
    return int(page.get_element_by_id("ContentPlaceHolder1_lblfrom").text.split(" ")[2])


def split_table(table: lh.HtmlElement):
    return table.getchildren()[0], table.getchildren()[1:]


def get_sc_judgements():
    pass


if __name__ == "__main__":
    # Get pmqs
    get_pmqs()

    # Get SC judgements
    get_sc_judgements()
