# PhishFry Remediation Library and Command Line Tool
PhishFry is a python library and command line tool for removing and restoring emails in exchange and office365. PhishFry supports shared mailboxes, group mailboxes and distribution lists. PhishFry removes/restores the entire conversation including any replies and forwards of the message.

## Installation
Install with pip directly from github.
```bash
sudo pip install git+https://github.com/ace-ecosystem/phishfry.git
```

Add credentials for one or more exchange accounts with impersonation rights to the config.ini file.
###### Example config.ini file:
```
[account1]
user=admin@example1.com
pass=123456

[account2]
user=admin@example2.com
pass=123456
```

## Command Line Tool
```bash
# display usage information
./phishfry.py -h

# Remove message with message_id=<message_id> from the test@example.com mailbox
./phishfry.py remove test@example.com "<message_id>"

# Restores message with message_id="<message_id>" to the test@example.com mailbox
./phishfry.py restore test@example.com "<message_id>"
```

## Library
```python
import phishfry

# Instantiate a phishfry account using admin email and password
account = phishfry.Account("admin@example1.com", "123456")

# remove a message
results = account.Remove("user@example1.com", "<message_id>")

# restore a message
results = account.Restore("user@example1.com", "<message_id>")

# using the results
for address in results:
	# print the email address for these results
	print(address)

	# get the remediation result for this address
	result = results[address]

	# print failure message if remediation action failed
	if not result.success:
		print(result.message)
```
