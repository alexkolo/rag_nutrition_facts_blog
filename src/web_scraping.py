import time

import requests
from bs4 import BeautifulSoup

REPLACEMENTS: dict[str, str] = {
    "“": "'",
    "”": "'",
    "’": "'",
    "‘": "'",
    "…": "...",
    "—": "-",
    "\u00a0": " ",
}

EXCLUDE_STARTSWITH: list[str] = [
    "Written By",
    "Image Credit",
    "In health",
    "Michael Greger",
    "-Michael Greger",
    "PS:",
    "A founding member",
    "Subscribe",
    "Catch up",
    "Charity ID",
    "We  our volunteers!",
    "Interested in learning more about",
    "Check out",
    "For more on",
]


def get_webpage_content(url: str, timeout: int = 10) -> requests.Response | None:
    try:
        response = requests.get(
            url, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

    return response


def filter_links(links: list[str], root: str) -> list[str]:
    filtered_links: list[str] = []
    for href in links:
        if not href.startswith(root):
            continue
        link_tail: str = href.replace(root, "")
        if link_tail and not link_tail.startswith("page"):
            filtered_links.append(href)

    return filtered_links


def extract_all_urls(
    root: str, page_stop: int | None = None, wait: float = 0.2
) -> list[str]:
    # collect all the blog posts urls
    i_page: int = 0
    url_list: list[str] = []
    while True:
        time.sleep(wait)  # wait a bit to avoid being blocked
        i_page += 1
        # for debug only
        if page_stop is not None and i_page > page_stop:
            break

        if i_page == 1:
            page_url = root
        else:
            page_url = f"{root}page/{i_page}/"
        print(f"{i_page}. Page URL: {page_url}")

        # get the HTML content
        response = get_webpage_content(page_url)
        if response is None:
            break

        # Parse the HTML content
        soup = BeautifulSoup(response.content, "html.parser")

        # get all links on the page
        links: list[str] = sorted(
            {link["href"] for link in soup.find_all("a", href=True)}
        )

        # filter the links
        blog_posts_of_page: list[str] = filter_links(links, root)
        n_posts: int = len(blog_posts_of_page)
        print(f"\t Number of blog posts: {n_posts}")
        # page needs at least 2 posts to be considered, otherwise it's at the last page
        if n_posts < 2:
            break
        url_list.extend(blog_posts_of_page)

    return url_list


def replace_strange_chars(text: str) -> str:
    # Create a dictionary for replacements to make the code more scalable
    return text.translate(str.maketrans(REPLACEMENTS))


def get_meta_data(soup: BeautifulSoup) -> dict:
    meta_data = {
        "title": soup.find("h1", class_="entry-title").get_text(),
        "created": soup.find("time", class_="updated")["datetime"],
        "updated": soup.find_all("time")[1]["datetime"],
    }
    return meta_data


def get_paragraphs(soup: BeautifulSoup) -> list[str]:
    paragraphs_html: list = soup.find_all("p", class_="p1")
    if not paragraphs_html:
        paragraphs_html = soup.find_all("p")

    # Extract and clean paragraphs while excluding those that start with certain phrases
    paragraphs_raw: list[str] = [
        replace_strange_chars(para_html.get_text().strip())
        for para_html in paragraphs_html
    ]

    # Create clean list
    paragraphs_clean: list[str] = [
        para_raw
        for para_raw in paragraphs_raw
        if para_raw
        and not any(para_raw.startswith(prefix) for prefix in EXCLUDE_STARTSWITH)
    ]
    return paragraphs_clean


def get_key_takeaways(soup: BeautifulSoup) -> list[str]:
    key_takeaways_heading = soup.find("p", string="KEY TAKEAWAYS")
    if key_takeaways_heading is None:
        return []

    # Find the next <ul> element after the "KEY TAKEAWAYS" heading
    key_takeaways_list = key_takeaways_heading.find_next("ul")

    # Extract the text from each <li> in the list
    return [
        replace_strange_chars(li.get_text().strip())
        for li in key_takeaways_list.find_all("li")
    ]


def extract_blog_data(soup: BeautifulSoup) -> dict:
    blog_content: dict = get_meta_data(soup)

    tags_raw = soup.find("article").get("class")
    blog_content["category"] = [
        cat.split("-")[1] for cat in tags_raw if cat.startswith("category-")
    ]
    blog_content["blog_tags"] = [
        tag.split("-")[1] for tag in tags_raw if tag.startswith("tag-")
    ]
    blog_content["raw_tags"] = tags_raw

    blog_content["paragraphs"] = get_paragraphs(soup)
    blog_content["key_takeaways"] = get_key_takeaways(soup)

    return blog_content
