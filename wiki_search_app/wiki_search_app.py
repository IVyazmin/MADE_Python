from flask import Flask, redirect, url_for, abort, render_template, request, jsonify
from markupsafe import escape
import requests
from lxml import etree


app = Flask(__name__)
WIKI_BASE_URL = "https://en.wikipedia.org"
WIKI_BASE_SEARCH_URL = f"{WIKI_BASE_URL}/w/index.php?search="


@app.route("/search")
def wiki_proxy_search():
	user_query = request.args.get("query", "")
	wiki_response = requests.get(WIKI_BASE_SEARCH_URL + user_query)
	return wiki_response.text, wiki_response.status_code


@app.route("/pretty_search")
def pretty_wiki_proxy_search():
	user_query = request.args.get("query", "")
	wiki_response = requests.get(WIKI_BASE_SEARCH_URL + user_query)
	if not wiki_response.ok:
		abort(503)

	documents = parse_wiki_search_output(wiki_response.text)
	return render_template(
		"wiki_search_result.html",
		query=user_query,
		documents=documents,
		wikipedia_base_url=WIKI_BASE_URL,
	)


@app.route("/api/search")
def api_wiki_proxy_search():
	user_query = request.args.get("query", "")
	wiki_response = requests.get(WIKI_BASE_SEARCH_URL + user_query)
	if not wiki_response.ok:
		abort(503)

	documents = parse_wiki_search_output(wiki_response.text)
	return jsonify({
		"documents": documents,
		"version": 1.0,
	})


def parse_wiki_search_output(wiki_search_output):
	root = etree.fromstring(wiki_search_output, etree.HTMLParser())
	documents_raw = root.xpath("//li[@class='mw-search-result']")
	documents = []
	for document in documents_raw:
		title = document.xpath(".//a[1]/@title")[0]
		link = document.xpath(".//a[1]/@href")[0]
		snippet = "".join(document.xpath(".//div[@class='searchresult']")[0].itertext())
		documents.append([title, link, snippet])

	return documents