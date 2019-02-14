# phishfry
python library and command line tool for remvoing/restoring emails in exchange/office365

## Command line examples
Delete a message from a maiblox
```bash
./phishfry.py delete test@example.com "<message_id>"
```

Restore a message to a mailbox
```bash
./phishfry.py restore test@example.com "<message_id>"
```

Display help command line help information
```bash
./phishfry.py -h
```

## Library usage
```python
from phishfry import RemediationAccount

account = RemediationAccount("outlook.office365.com", "admin@example.com", "password123")
for address in account.resolve_name("user@example.com"):
    account.delete(address, "<message_id>")
```
