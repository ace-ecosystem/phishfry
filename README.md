# PhishFry Remediation Library and Command Line Tool
PhishFry is a python library and command line tool for removing and restoring emails in exchange and office365.

## Installation
Install exchangelib.
```bash
sudo pip install git+https://github.com/ecederstrand/exchangelib.git
```

Clone the phishfry repo.
```bash
git@github.com:IntegralDefense/phishfry.git
```

Ignore changes to credentials file.
```bash
cd phishfry
git update-index --assume-unchanged credentials
```

Add your exchange account credentials to the credentials file with the following format:
```
exchange_server:admin_email_address:admin_email_password
```
Example credentials file:
```
outlook.office365.com:admin@example.com:password
```
NOTE: Your exchange account must have impersonation rights in exchange to perform delete and restore operations.

## Command Line Tool
```bash
# display usage information
./phishfry.py -h

# Deletes message with message_id=<message_id> from the test@example.com mailbox
./phishfry.py delete test@example.com "<message_id>"

# Restores message with message_id="<message_id>" to the test@example.com mailbox
./phishfry.py restore test@example.com "<message_id>"
```

## Library
```python
import remediation

# instantiate a remediation account
account = remediation.Account("outlook.office365.com", "admin@example.com", "password123")

# resolve a user address into all recipient addresses
addresses = account.resolve_name("user@example.com")

# delete a message from all recipients' mailboxes
for address in addresses:
	try:
		account.delete(address, "<message_id>")
	except Exception as e:
		print(e)

# restore a message to all recipients' mailboxes
for address in addresses:
	try:
		account.restore(address, "<message_id>")
	except Exception as e:
		print(e)
```
