# Thanks L and P from Discord Python, you know who you are.
null = None
d = {
  "1": {
    "metadata": {
      "category_id": 1,
      "name": "Movies",
      "slug": "movies",
      "image": null,
      "provides": "video",
      "protocol": "ipfs",
      "populated": "1"
                 }
        }
     }
for i in d.values():
  print(i['metadata']['name'])