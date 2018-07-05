import urllib
import argparse

import wikipedia
from bs4 import BeautifulSoup

import pickle
import sys, os
#sys.stderr = None

template = "https://wikipedia.org"    

def isValid(ref,paragraph):
	if not ref or "#" in ref or "//" in ref or ":" in ref:
		return False
	if "/wiki/" not in ref:
		return False
	if ref not in paragraph:
		return False
	return True

def validateTag(tag):
	name = tag.name
	isParagraph = name == "p"
	isList = name == "ul"
	return isParagraph or isList

def rnd():
	try:
		res = wikipedia.random()
	except wikipedia.exceptions.DisambiguationError:
		return rnd()
	return res

def pageFormat(page):
	out = urllib.parse.unquote(page.replace(')', '').replace('(', '').replace('_', ' '))

	return out

def pageToHtml(page):
	page = pageFormat(page)
	try:
		return wikipedia.page(page).html()
	except wikipedia.exceptions.DisambiguationError as e:
		return pageToHtml(e.args[1][0])

linkCache = {}

def getFirstLink(html):
	soup = BeautifulSoup(html, 'lxml')
	soup = soup.find("div", {"class": "mw-parser-output"})

	for paragraph in soup.find_all(["p", "ul"], recursive=False):
		for link in paragraph.find_all("a"):
			ref = link.get("href")
			if isValid(str(ref),str(paragraph)):
				return link
	return False

def linkToTitle(l):
	return pageFormat(l['href'].split('/wiki/')[1])

def getNextArticle(article):
	#if article == "TEST_TEST123":
	#    h = test_html
	#else:
	h = pageToHtml(article)
	l = getFirstLink(h)
	return linkToTitle(l)

cachePath = 'cache.pickle'

def load_cache():
	if os.path.isfile(cachePath):
		with open(cachePath, 'rb') as f:
			global linkCache
			linkCache = pickle.load(f)

def save_cache():
	with open(cachePath, 'wb') as f:
		pickle.dump(linkCache, f)

program_out = ""

def print_out(st):
	print(st)
	global program_out
	program_out += st + '\n'

def run(target, start):
	if start is None:
		start = rnd()
	visited = {}

	current = start
	visited[current] = True

	while True:
		if current in linkCache:
			nxt = linkCache[current]
		else:
			nxt = getNextArticle(current)
			linkCache[current] = nxt

		current = nxt

		print_out(current)
		if visited.get(current, False):
			print_out("Found a loop! Exiting")
			return
		elif current == target:
			print_out("Reached target")
			return
		visited[current]=True

def run_indefinitely(target, start=None):
	try:
		while True:
			print_out('') #newline
			run(target, start)
	except KeyboardInterrupt:
		print("Received interrupt, stopping...")

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Wikipedia tool that starts from a given (or random) article, visiting every first link until a given target article is found or a loop is encountered.")
	parser.add_argument('--start', type=str, default=None, help='The starting article. Random by default.')
	parser.add_argument('--file', type=str, default=None, help='Save the program output to a file.')
	parser.add_argument('--loop', dest='loop', action='store_true', help='Run indefinitely until a keyboard interrupt (Ctrl+C) is received.')
	parser.add_argument('target', type=str, help='The target artigle.')
	parser.set_defaults(loop=False)
	args, _ = parser.parse_known_args()
	
	load_cache()
	if args.loop:
		run_indefinitely(args.target, args.start)
	else:
		run(args.target, args.start)
	save_cache()

	if args.file is not None:
		with open(args.file, 'w') as f:
			f.write(program_out)

