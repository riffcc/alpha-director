# The Director
The Director is a special research project of the Riff.CC project, intended to completely decentralise the primary mechanisms that allow Riff.CC-based streaming services to operate.

See `DOCUMENTATION.md` for instructions on usage.

## Purpose
The Director creates a JSON-based "pseudo-API" suitable for consumption by applications, both SPA and traditional.

It is intended to create a package of metadata which can be stored entirely on IPFS and loaded as needed.

## Credits
The Director would not have been possible without the following:

* JetBrains generously providing tools for our open source development

## Scratchpad
if releases_per_page = 50 and api_page_size = 15
    fetch 15 to buffer
    fetch 15 to buffer
    fetch 15 to buffer
    fetch 15 to buffer
    move 50 to new_page, remainder 10
    fetch 15 to buffer
    fetch 15 to buffer
    fetch 15 to buffer
    move 50 to new page, remainder 5
    fetch 15 to buffer
    fetch 15 to buffer
    fetch 15 to buffer
    move 50 to new page.
    repeat until fetch returns last_page_reached