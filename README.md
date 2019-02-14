# PhishFry Remediation Library and Command Line Tool
PhishFry is a python library and command line tool for removing and restoring emails in exchange and office365.

## Installation
Clone the repo and run the setup script.
```bash
git@github.com:IntegralDefense/phishfry.git
cd phishfry
./setup.sh
```

Add credentials for one or more exchange accounts with impersonation rights to the credentials file.
Example credentials file:
```
# exchange_server:admin_email_address:admin_email_password
outlook.office365.com:admin@example.com:password
```

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
