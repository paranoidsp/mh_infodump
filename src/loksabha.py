from typing import List, Dict
import requests as r

from .constants import LS_URL, LS_TABLE_XPATH, FILE_DOWNLOAD_BASE_PATH

# Okay, I know bs4 exists, but I assumed lxml was in the python stdlib
# and that I wouldn't need to install it for github actions, but turns out it
# isn't, and now sunk cost fallacy has me
# So ignore the magic xpath parsing all over the page, and fix the script if
# the website changes.
import lxml.html as lh
import os


class LokSabhaQuestions:
    """
    Get Lok Sabha Qs about mental health
    """

    def __init__(self, download_path: str, topics: List[str]):
        self.topics = topics
        self.download_path = download_path
        self.results_by_date = {}
        self.url = LS_URL
        self.table_xpath = LS_TABLE_XPATH

    def get_qs(self) -> None:

        # Lok Sabha search page needs a bunch of session variables to be sent along
        # with a search query. These variables change each time the page is loaded.
        # So we'll first get the page without searching, store those variables and use
        # them to send an actual search query
        # This is generally the standard scraping technique for aspx forms
        # You could do this cleaner with the scrapy library, but 
        # this will do for a simple form like this
        
        # Load the basic search page
        resp = r.get(self.url, timeout=5)
        parsed_resp = lh.fromstring(resp.text)

        # Set up our search query, and store the special variables from the search page
        # The rest of them are captured from a search run through the webpage
        INITIAL_DATA = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": parsed_resp.get_element_by_id("__VIEWSTATE").value,
            "__VIEWSTATEGENERATOR": parsed_resp.get_element_by_id(
                "__VIEWSTATEGENERATOR"
            ).value,
            "__VIEWSTATEENCRYPTED": "",
            "__EVENTVALIDATION": parsed_resp.get_element_by_id(
                "__EVENTVALIDATION"
            ).value,
            "ctl00$txtSearchGlobal": "",
            "ctl00$ContentPlaceHolder1$ddlfile": ".pdf",
            "ctl00$ContentPlaceHolder1$TextBox1": self.topics[0],
            "ctl00$ContentPlaceHolder1$btn": "allwordbtn",
            "ctl00$ContentPlaceHolder1$btn1": "titlebtn",
            "ctl00$ContentPlaceHolder1$txtpage": "1",
        }

        # Getting a specific page requires the Go button
        search_data = INITIAL_DATA
        search_data["ctl00$ContentPlaceHolder1$btngo"] = "Go"

        # search page 1
        search_resp = r.post(self.url, search_data, timeout=10)
        parsed_search = lh.fromstring(search_resp.text)

        # Get total number of pages
        num_pages = self.get_num_pages(parsed_search)
        print(f"Found {num_pages} pages of results, fetching them all...")

        results = []

        # paginate through them, get first row again just because I'm lazy
        for page in range(1, num_pages + 1):
            rows = self.get_results_from_page(search_data, page)
            for row in rows:
                q_info = self.get_q_info(row.xpath("td"))

                if q_info == {}:
                    print(f"Failed to parse row")
                    exit(0)

                if not q_info["date"] in self.results_by_date:
                    self.results_by_date[q_info["date"]] = {}

                self.results_by_date[q_info["date"]][q_info["q_no"]] = q_info

                print(
                    f"Found question number {q_info['q_no']}, by {q_info['members']} on {q_info['date']}"
                )
            print(f"=> Found {len(rows)} results from page {page}")
            results.extend(rows)

        print("----------------------------------")
        print(f"Found a total of {len(results)} results!")

        self.save_files()

    def save_files(self):
        base_path = os.path.join(
            self.download_path,
            FILE_DOWNLOAD_BASE_PATH,
            "lok-sabha-q",
        )

        if not os.path.exists(base_path):
            os.mkdir(base_path)
            
        print("----------------------------------")
        print("Saving files")

        changed = {}

        for date, questions in self.results_by_date.items():
            print(f"Checking date {date}")
            for q_no, q_info in questions.items():
                print(f"=> Checking question {q_no}")
                # file path
                date_path = os.path.join(base_path, date)
                file_path = os.path.join(date_path, str(q_no) + ".pdf")

                # Exact file exists, skip
                if os.path.isfile(file_path):
                    print(f"    Already Exists")
                    continue
                else:
                    # log changes
                    if not date in changed:
                        changed[date] = []

                    changed[date].append(q_no)
                    # if date folder doesn't exist, create it
                    if not os.path.isdir(date_path):
                        os.mkdir(date_path)

                    # Get the file
                    resp = r.get(q_info["url"], allow_redirects=True, timeout=5)

                    with open(file_path, "wb") as f:
                        f.write(resp.content)

                    print(f"  ... File Written!")

        total_changed = sum([len(x) for x in changed.values()])
        print(f"Found {total_changed} changes!")

    def get_q_info(self, columns) -> Dict:
        q_info = {}

        # Since q_no and date are what we want to use to find file path, we
        # must validate them

        # Q_no is the text in the second link
        # validate that it is an int
        try:
            q_info["q_no"] = int(columns[0].xpath("a")[1].text)
        except ValueError:
            print("Parsing error: Website format seems to have changed")
            return {}

        # url needs to be for the english version
        for link in columns[1].xpath("a"):
            if link.text == "PDF/WORD":
                q_info["url"] = link.attrib["href"]

        # date, validate to make sure it looks good
        for link in columns[2].xpath("a"):
            # There are two links in each columns
            # First one just has id
            # Second one has the actual text and the link itself
            # We want the text
            if "href" in link.attrib:
                q_info["date"] = link.text
                assert (
                    len(q_info["date"].split(".")) == 3
                ), "Parsing error: Website format seems to have changed"

        # ministry
        q_info["ministry"] = columns[3].xpath("a")[1].text

        # Members and subject
        # Members are each on separate hyperlink tags
        # strip to avoid all the extra spaces
        q_info["members"] = "".join(columns[4].itertext()).strip()
        q_info["subject"] = "".join(columns[5].itertext()).strip()

        return q_info

    def get_headers(self, page: lh.HtmlElement):
        # using xpath for now
        table = page.xpath(self.table_xpath)[0]
        headers = [td.text.strip() for td in table.xpath("thead/tr/td")]

        return headers

    def get_results_from_page(self, data: Dict[str, str], page: int):
        # set page number
        data["ctl00$ContentPlaceHolder1$txtpage"] = str(page)

        # fetch and parse
        search_resp = r.post(self.url, data, timeout=10)

        return self.parse_page(lh.fromstring(search_resp.text))

    def parse_page(self, page: lh.HtmlElement):
        # using xpath for now
        table = page.xpath(self.table_xpath)[0]

        return table.xpath("tr")

    def get_num_pages(self, page: lh.HtmlElement) -> int:
        return int(
            page.get_element_by_id("ContentPlaceHolder1_lblfrom").text.split(" ")[2]
        )
