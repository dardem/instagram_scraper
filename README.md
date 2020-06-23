# Instagram Scrapper

Tool for parsing Instagram search pages by hashtags.

Yes, it is quite difficult to parse from Instagram. There are some tools for parsing personal pages. However, it is more interesting to make search by some hashtag and parse the search results.

So, how does the magic work? The main panch: all operations with Instagram is produced via imitation of page opening and scrolling. As a result, here are some prerequisites:
* you should be logged in Instagram profile in your browser: it can be some test profile or even your know;
* (for now) you should have Firefox browser and its driver (already in repo).

## Settings

In the file `setting/general.py` you should define:
* the path to your browser;
* tags, on which you want to make search.

## Launch

The main file for execution is `main.py`. 
