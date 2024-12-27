### Preps
```sh
python -m venv venv; source venv/bin/activate
pip install -r requirements.txt
```

### Database creation
```sh
./makesqlite.sh
```

### Running locally
```sh
./main.py
```

### Serving as ssh-based app (requires golang compiler)
#### prep
```sh
go build serve.go
```
#### run
```sh
./serve <host> <port> $(pwd)/main.py
# e.g.
./serve localhost 23234 $(pwd)/main.py
```

TODO:
- [ ] wyświetlanie wypożyczeń
- [ ] edytowanie zaklęć
- [ ] wyszukiwanie zaklęć
