# A brief summary
BCH SLP is used to create a chain of trust of signing keys which can be revoked as needed, which certify and sign an IPFS hash pointing to a JSON data file.

The JSON then points to other IPFS hashes as needed, forming a tree that allows access to all data needed to load Riff.CC content. We can modify the contents of that JSON, publish it to IPFS and then store a pointer to the hash as an OP_RETURN code in the signing wallet. For additional security, we can sign that root IPFS hash and store the signature on the gateway, and instruct any Riff.CC clients to only load the data inside it if the signature matches the associated key pair.

We can revoke dead signing keys by simply making a new one and making the app compare the new and old keys after getting the new key from the Origin Root service.

By checking the block height of the SLP tokens as they enter Wallet A, you can easily validate that they are newer or older in each signing wallet.

The implementation of such a system with open and transparent code would allow any platform to create their own "view" of the world, consuming Riff.CC's content and user bandwidth in a symbiotic fashion, or some other set of content or some combination of both.
