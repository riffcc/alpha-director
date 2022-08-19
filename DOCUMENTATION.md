Purpose
=======
* The Director is a tool used to "transpile" a regular "Unit3D CE" 
  based private tracker from its native MySQL-based relational database,
  into a parseable metadata tree that a browser can easily parse.

* This provides a middle ground between "NoSQL" and "Relational" that allows
  clients to quickly and easily retrieve metadata about the site.

* The cost of storing this metadata goes up over time with each run of The Director,
  but because of the nature of the software (and its reliance on IPFS), in practice
  only the files that have changed will actually need to be stored on IPFS again.

* As a platform, we store the "best format" version of a movie as an additional field in Unit3D,
  which The Director retrieves during its run, and publishes to IPFS.

* Upon completion of the run, The Director stores a "magic locator" beacon that allows clients to
  retrieve the complete platform data as it stands.

* In the future, we will ask our power users to join our IPFS Cluster as followers and maintain the metadata set.

Requirements
============

* A modern Python3 stack (tested on Python 3.9.5 on macOS Big Sur version 11.2.2)

* A functional Unit3D installation somewhere, with SSH keys setup that allow for passwordless authentication.

Testing environment
===================
* Riff.CC @ https://github.com/riffcc/platform/commit/16cee87ee56ebc40d6ff1728481ebba26b08f723
  (based on Unit3D v5.2.0 as of 2021-07-29)

Setup
=====
* Create a file "~/.rcc-api" with the API key of an unprivileged user who can only view torrents (we called ours "Stream")

  `cp examples/.rcc-api.dist ~/.rcc-api`

* Create a file "~/.rcc-tools.yml" with the sensitive database credentials, ~/.rcc-tools.yml.example provided

  `cp examples/.rcc-tools.dist ~/.rcc-tools.yml
