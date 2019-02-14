# PhishFry
PhishFry is a python library and command line tool for removing and restoring emails in exchange and office365.

## Setup
### Install exchangelib
PhishFry requires the exchangelib python package. Run the following commands to install exchangelib:
```bash
git clone git@github.com:ecederstrand/exchangelib.git
cd exchangelib
sudo python3 setup.py install
```

### Configure Credentials
Add your exchange account credentials to the credentials file with the following format:
```
exchange_server:admin_email_address:admin_email_password
```
Example credentials file:
```
outlook.office365.com:admin@example.com:password
```
NOTE: Your exchange account must have impersonation rights in exchange to perform delete and restore operations.

## Command line examples
#### Delete a message from a maiblox
```bash
./phishfry.py delete test@example.com "<message_id>"
```

#### Restore a message to a mailbox
```bash
./phishfry.py restore test@example.com "<message_id>"
```

#### Display help command line help information
```bash
./phishfry.py -h
```

## Library usage
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
