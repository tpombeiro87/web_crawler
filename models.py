#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import hashlib
import io
import re
import json

from bs4 import BeautifulSoup
import pycurl
import sys


SLASH_PATTERN = re.compile(ur'^/+.*')


class SiteMap(object):

    def __init__(self, domain, content):
        self.domain = domain
        self.internal_nodes = {}
        self.external_nodes = {}
        self.internal_nodes[domain] = SiteMapNode(loc=domain, depth=1, content=content, visited=False)

    def get_domain_node(self):
        return self.internal_nodes[self.domain]

    def add_node(self, link, parrent_depth, content):
        link = link.split('#', 1)[0]
        loc = self.domain + link
        internal_node = None

        if len(link) > 1:
            if SLASH_PATTERN.match(link) is not None and loc not in self.internal_nodes:
                internal_node = SiteMapNode(loc=loc, depth=parrent_depth + 1, content=content, external=False, visited=False)
                self.internal_nodes[internal_node.loc] = internal_node

            elif SLASH_PATTERN.match(link) is None and link not in self.internal_nodes:
                node = SiteMapNode(loc=link, depth=parrent_depth + 1, content=content, external=True, visited=False)
                self.external_nodes[link] = node

        return internal_node

    def wrap_up_node(self, node, status, tree):
        if node.external:
            # just to for the future not used on the context of this task
            self.external_nodes[node.loc].set_status(status)
            self.external_nodes[node.loc].set_visited(True)
            self.external_nodes[node.loc].set_assets(tree, self.domain)
        else:
            self.internal_nodes[node.loc].set_status(status)
            self.internal_nodes[node.loc].set_visited(True)
            self.internal_nodes[node.loc].set_assets(tree, self.domain)

    def get_size(self):
        return len(self.internal_nodes)

    def get_visited(self):
        return filter(lambda node: node.visited, self.internal_nodes.values())

    def ratio_visited(self):
        return float(len(self.get_visited())) / float(self.get_size())

    def to_string(self, file_name=None, simple_output=False):
        if file_name:
            sys.stdout = open(file_name, 'w')

        intenal_node_json = map(lambda node: node.get_json_representation(), self.get_visited())
        if simple_output:
            sys.stdout.write('[')
            for counter, node in enumerate(intenal_node_json):
                json.dump(node, sys.stdout)
                if counter != len(intenal_node_json) - 1:
                    sys.stdout.write(',\n')
            sys.stdout.write(']')
        else:
            sys.stdout.write(json.dumps(intenal_node_json, sort_keys=False, indent=4))


class SiteMapNode(object):

    def __init__(self, loc, depth, content=None, external=False, visited=False):
        self.loc = loc
        if content:
            pass
            # self.content_hash = self.my_hash(content)
        self.assets = []
        self.status = None
        self.depth = depth
        self.external = external
        self.visited = visited

    def set_assets(self, tree, domain):
        # pair of elements and assets url identification
        elements_pairs = [('script', 'src'), ('img', 'src'), ('meta', 'content'), ('link', 'href'), ]
        for element_pairs in elements_pairs:
            (element, url_atribute) = element_pairs
            for e in tree.findAll(element):
                asset_link = e.attrs.get(url_atribute, "")
                domain_striped = domain.replace('www.', '')
                if (len(asset_link) > 1 and asset_link[-1] != "/" and not asset_link.endswith(domain_striped) and
                        not asset_link.endswith(domain_striped) and not asset_link.startswith('//') and
                        (SLASH_PATTERN.match(asset_link) is None or domain_striped in asset_link)):
                    self.assets.append(asset_link)

    def set_status(self, status):
        self.status = status

    def set_visited(self, visited):
        self.visited = visited

    def my_hash(self, content):
        # just to for the future not used on the context of this task
        return hashlib.sha224(content).hexdigest()

    def get_json_representation(self):
        return {
            'loc': self.loc,
            'status': self.status,
            'depth': self.depth,
            # 'content:hash': self.content_hash,
            'assets': self.assets,
            'external': self.external,
            'visited': self.visited
        }


class Browser(object):

    def __init__(self, timeout=3):
        # private vars
        self._c = pycurl.Curl()

        # public vars
        self.html = ""
        self.tree = BeautifulSoup(self.html, "html5lib")
        self.match = None

        # default options
        self._c.setopt(pycurl.FOLLOWLOCATION, True)
        self._c.setopt(pycurl.TIMEOUT, timeout)

    def close(self):
        self._c.close()

    """
    Browsing
    """

    def go(self, url):
        self._c.setopt(pycurl.HTTPGET, 1)
        result = io.BytesIO()
        self._c.setopt(pycurl.WRITEDATA, result)
        self._c.setopt(pycurl.URL, url)

        try:
            self._c.perform()
        except pycurl.error as detail:
            raise BrowserException('Url %s not reachable response code: %d detail: %s' % (self.get_effective_url(), self.get_code(), detail))

        # get the result of the request
        self.html = result.getvalue()

        # parse the result
        self.tree = BeautifulSoup(self.html, "html5lib")

    """
    Assertions
    """

    def code(self, code):
        return (self._c.getinfo(pycurl.RESPONSE_CODE) == code)

    def find(self, regexp):
        self.match = re.search(regexp, self.html, re.DOTALL)
        return (self.match is not None)

    def find_many(self, regexps):
        if type(regexps) != list:
            regexps = [regexps]

        for rg in regexps:
            self.match = re.search(rg, self.html, re.DOTALL)
            if self.match is None:
                return False
        return True

    """
    Gets
    """

    def get_code(self):
        return self._c.getinfo(pycurl.RESPONSE_CODE)

    def get_content_type(self):
        return self._c.getinf(pycurl.CONTENT_TYPE)

    def get_time(self):
        return self._c.getinfo(pycurl.TOTAL_TIME)

    def get_size(self):
        return self._c.getinfo(pycurl.SIZE_DOWNLOAD)

    def get_effective_url(self):
        return self._c.getinfo(pycurl.EFFECTIVE_URL)

    def get_html(self):
        return self.html


class BrowserException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
