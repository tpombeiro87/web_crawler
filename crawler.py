#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import Queue as queue

import argparse
import re
import sys
import threading
import time

import models

DEFAULT_SITE_TO_CRAWL = "www.google.com"
DEFAULT_OUTPUT        = "result.json"
DEFAULT_LIMIT         = 100

SIMPLE_OUTPUT = False
DEBUG         = True

PYCURL_TIMEOUT = 15  # IN SECONDS


def collect_args():
    # Main parser
    parser = argparse.ArgumentParser(description="WEB CRAWLER TASK")
    parser.add_argument("-u", "--url",           type=str, default=DEFAULT_SITE_TO_CRAWL, help="The site domain you want to crawl. Default: '%s'" % DEFAULT_SITE_TO_CRAWL)
    parser.add_argument("-f", "--output_file",   type=str, default=DEFAULT_OUTPUT,        help="File to output the resulting site map. Default goes to the file 'result.json'.")
    parser.add_argument("-l", "--limit_pages",   type=int, default=DEFAULT_LIMIT,          help="Limit of how many sites should be crawlled. Defaul 100. 0 defines no limit.")
    parser.add_argument("-s", "--simple_output", type=bool, default=SIMPLE_OUTPUT,         help="Defines the indentation to be adopted on output to be printed to the file. If True (default) - prints each node per line. If False prints each node with indentation.")
    parser.add_argument("-d", "--debug",         type=bool, default=DEBUG,                 help="If you want to run this in debug mode (more info on prints). Default is False")
    args = parser.parse_args()

    url_pattern = re.compile(ur'^(http(s)?://)*(www.)([a-zA-Z]){1,}.([a-zA-Z]){2,3}$')
    if url_pattern.match(args.url) is None:
        raise Exception("Url '%s' is not valid." % args.url)

    if args.limit_pages < 0:
        raise Exception("Limit pages cannot be a negative number.")

    return (args.url, args.output_file, args.simple_output, args.debug, args.limit_pages)


def log(msg, force_print=False, with_paragrahp=True):
    if force_print:
        msg = msg + "\n" if with_paragrahp else msg
        sys.stdout.write(msg)


class EvalPageThread (threading.Thread):
    def __init__(self, node, debug):
        threading.Thread.__init__(self)
        self.node = node
        self.debug = debug

    def run(self):
        global site_map
        browser = models.Browser(PYCURL_TIMEOUT)
        try:
            log('. %s' % self.node.loc, self.debug)
            log('.', not self.debug, False)

            browser.go(self.node.loc)
            for anchor in browser.tree.findAll("a"):
                link = anchor.attrs.get("href", "")

                threadLock.acquire()  # Get lock to synchronize threads
                internal_node = site_map.add_node(link, self.node.depth, browser.get_html())
                if internal_node:
                    queue.put(internal_node)
                threadLock.release()  # Free lock to release next thread

        except models.BrowserException as e:
            log('\n- Exception: %s \n' % e, self.debug)
        finally:
            threadLock.acquire()  # Get lock to synchronize threads
            site_map.wrap_up_node(self.node, browser.get_code(), browser.tree)
            threadLock.release()  # Free lock to release next thread

# -- INITIALIZATION --

browser = None
debug = DEBUG


# ---------------------- START MAIN ----------------------

if __name__ == "__main__":

    try:
        start_time = time.time()
        (domain, output_file, simple_output, debug, limit_pages) = collect_args()
        log('---- START CRAWLING: %s' % domain, True)
        counter = 1
        threads = []
        browser = models.Browser(PYCURL_TIMEOUT)
        threadLock = threading.Lock()
        queue = queue.Queue()

        browser.go(domain)
        site_map = models.SiteMap(domain, browser.get_html())

        queue.put(site_map.get_domain_node())

        while site_map.get_size() == 1 or site_map.ratio_visited() < 1:
            if not queue.empty():
                node = queue.get()
                t = EvalPageThread(node, debug)
                counter += 1
                t.start()
                threads.append(t)
            if counter > limit_pages and limit_pages != 0:
                break

        # Wait for all threads to complete
        for t in threads:
            t.join()

        if limit_pages != 0:
            log('\n--- END - Execution time %s seconds for the set limit of %d pages' % (time.time() - start_time, limit_pages), True)
        else:
            log('\n--- END - Execution time %s seconds for %d pages' % (time.time() - start_time, site_map.get_size()), True)
        # Print result to file
        site_map.to_string(output_file, simple_output)

    except Exception as e:
        log('--- Exception: %s' % e, debug)
        if debug:
            import traceback
            traceback.print_exc()
    finally:
        if browser:
            browser.close()
        sys.stdout.close()
