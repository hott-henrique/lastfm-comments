import argparse, contextlib, datetime, json, random, sys, time

import tqdm

from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.remote.webelement import WebElement


@contextlib.contextmanager
def file_or_stdout(filename: str, mode: str):
    if filename:
        fh = open(filename, mode)
    else:
        fh = sys.stdout

    try:
        yield fh
    finally:
        if fh is not sys.stdout:
            fh.close()

def process_comments_container(comments_we: list[WebElement], ids_collected: list = list()):
    comments = list()

    for comment_we in comments_we:
        comment = process_comment_we(comment_we=comment_we, ids_collected=ids_collected)

        if comment:
            comments.append(comment)

    return comments

def process_comment_we(comment_we: WebElement, ids_collected: list = list()):
    try:
        id = comment_we.get_attribute("id")

        id = id.strip() if id else ""

        if id not in ids_collected:
            ids_collected.append(id)
        else:
            return None

        user_we = comment_we.find_element(By.CLASS_NAME, "shout-user")
        content_we = comment_we.find_element(By.CLASS_NAME, "shout-body")
        date_we = comment_we.find_element(By.TAG_NAME, "time")
        votes_we = comment_we.find_element(By.CLASS_NAME, "vote-button")

        user = user_we.get_attribute("innerText")
        content = content_we.get_attribute("innerText")
        votes = votes_we.get_attribute("innerText")
        date = date_we.get_attribute("datetime")

        user = user.strip() if user else ""
        content = content.strip() if content else ""
        votes = int("".join(filter(str.isnumeric, votes))) if votes else ""
        date = date.strip() if date else None

        responses_we = comment_we.find_elements(By.CLASS_NAME, "shout-list-item")

        responses = process_comments_container(responses_we, ids_collected=ids_collected)

        return dict(user=user, content=content, votes=votes, date=date, responses=responses)
    except:
        return None

def main(pagination_url: str, waiting: float, output_file: str):
    driver = Chrome()

    driver.get(pagination_url)

    pages_we = driver.find_elements(By.CLASS_NAME, "pagination-page")

    first_page = pages_we[0].get_property("innerText")
    last_page = pages_we[-1].get_property("innerText")

    first_page, last_page = int(first_page), int(last_page)

    with file_or_stdout(output_file, "w") as f:
        for page in tqdm.tqdm(range(first_page, last_page + 1), desc="Collecting comments"):
            driver.get(pagination_url + f"&page={page}")

            WebDriverWait(driver, 10).until(presence_of_element_located((By.CLASS_NAME, "shoutbox")))

            comments_we = driver.find_elements(By.CLASS_NAME, "shout-list-item")

            for comment in process_comments_container(comments_we=comments_we):
                tqdm.tqdm.write(json.dumps(comment), file=f)

            time.sleep(random.random() * waiting)

    driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--pagination-url", type=str, required=True)
    parser.add_argument("--output-file", type=str, default="", required=False)
    parser.add_argument("--waiting", type=float, default=30, required=False)

    args = parser.parse_args()

    main(pagination_url=args.pagination_url, waiting=args.waiting, output_file=args.output_file)
