WEB CRAWLER TASK
===============


What is?
-------------

A simple web crawler, which given a URL to crawl, outputs:
 * a site map showing the static assets for each page. 

It is not limited to one domain - so when crawling google.com it would :
 * crawl all pages within the google.com domain, 
 * but not follow external links.


Requirements?
-------------

In order to run this task you should have the following installed:
* Python 2.7


Design Decisions
----------------

Here follows a description of the files and whats their purpose:

    web_crawler
    ├── crawler.py    - file that contains the logic that parameter parser's and thread management for the crawler
    ├── models.py     - defines the classes that represent the site map nodes browser and others
    ├── README.md     - Instruction about the task and how to run it
    └── result.json   - Where the site map result will be outputted by default (the current content of the file was a 100 limit crawl to the domain google.com)

The models contain 3 important classes definitions:
  * Browser - that has the objective of impersonating a browser and to make the actions needed to get the webpages
  * Node    - Represents one page of the site map. contains the location, http status, and the assets the page has
  * SiteMap - The objective of this class is to group the nodes that represent the pages within a domain. Its purpose is to allocate and decide which nodes should be on the site map

The crawler file has the logic regarding the threads management. This approach was selected for performance purposes.


How to run?
-----------

In order to run this task the procedure is simple by using the following command on the context of this folder:
    $ python crawler.py -u <DOMAIN> -f <FILE_OUTPUT> -l <LIMIT_PAGES> -s <SIMPLE_OUTPUT> -d <DEBUG>

<DOMAIN> - The site domain you want to crawl. Default: 'www.google.com'
<FILE_OUTPUT> - File to output the resulting site map. Default goes to the file 'result.json
<LIMIT_PAGES> - Limit of how many sites should be crawlled. Default 100. 0 defines no limit
<FILE_OUTPUT> - Defines the indentation to be adopted on output to be printed to the file. If True (default) - prints each node per line. If False prints each node with indentation
<SIMPLE_OUTPUT> - Defines the indentation to be adopted on output to be printed to the file. If True (default) - prints each node per line. If False prints each node with indentation
<DEBUG> - If you want to run this in debug mode (more info on prints). Default is False. If this option is ennabled some exceptions will appear that are expected exceptions like http 301 and timeout.

No argummets are mandatory but is recommended that this command example is used:  

    $ python crawler.py -u www.google.com -l 0 -d True


Done by 
-------

This was a task developed by Tiago Pombeiro.