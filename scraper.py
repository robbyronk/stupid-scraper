import pickle
from time import sleep
from urlparse import urlparse, urljoin
import urllib2
from bs4 import BeautifulSoup
from tablib import Dataset

urls_filename = 'urls-to-scrape.txt'
bad_domains_filename = 'bad-domains.txt'
already_scraped_filename = 'already-scraped.txt'
from_to_filename = 'from-to.csv'
pickle_filename = 'from-to.p'

# load urls to scrape
# load the banned domains
# load the already scraped list
with open(urls_filename) as u, open(bad_domains_filename) as b, open(already_scraped_filename) as a:
    urls = u.read().splitlines()
    bad_domains = b.read().splitlines()
    already_scraped = a.read().splitlines()

# take the first url as the input url
input_url = urls[0]

# write out the rest of the urls to scrape to file
rest_of_urls = urls[1:]
with open(urls_filename, 'w') as u:
    for url in set(rest_of_urls):
        u.write('{}\n'.format(url))

# parse the input url
parsed_input_url = urlparse(input_url)

# if the domain is bad or the url has already been scraped, exit
input_domain = parsed_input_url.netloc
is_bad_domain = input_domain in bad_domains
is_already_scraped = input_url in already_scraped
is_bad_scheme = parsed_input_url.scheme not in ['http', 'https']
if is_bad_domain or is_already_scraped or is_bad_scheme:
    exit()

# get the html
resp = urllib2.urlopen(input_url)

# get the values of a[href]
soup = BeautifulSoup(resp, from_encoding=resp.info().getparam('charset'))
all_a_tags = soup.find_all('a', href=True)
all_hrefs = {a_tag['href'] for a_tag in all_a_tags}  # set comprehension for unique urls

# filter out urls that start with '#'
all_links = [href for href in all_hrefs if href and href[0] != '#']

# group urls by domain
try:
    from_to = pickle.load(open(pickle_filename, 'rb'))
except:
    from_to = {}
by_domain_count = from_to.get(input_domain, {})
for url in all_links:
    p = urlparse(url)
    if p.netloc and p.netloc != input_domain:
        count = by_domain_count.get(p.netloc, 0)
        by_domain_count[p.netloc] = count + 1
from_to[input_domain] = by_domain_count
pickle.dump(from_to, open(pickle_filename, 'wb'))

# write from-to-domain count
from_to_count = Dataset()
from_to_count.headers = ('from', 'to', 'count')
for _from, to_count in from_to.iteritems():
    for to, count in to_count.iteritems():
        from_to_count.append((_from, to, count))
with open(from_to_filename, 'w') as ft:
    ft.write(from_to_count.csv)

# add the scheme and domain to relative urls
# add the scheme to scheme relative urls
# remove fragment from url
urls_to_scrape = [urljoin(input_url, url, allow_fragments=False) for url in all_links]

# append urls to to-be-scraped
with open(urls_filename, 'a') as u:
    for url in urls_to_scrape:
        u.write('{}\n'.format(url))

# append input url to already-scraped
with open(already_scraped_filename, 'a') as a:
    a.write('{}\n'.format(input_url))

sleep(1) # be nice to web servers