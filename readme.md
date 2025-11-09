# Setup

## Windows

### Automatic
```
.\play_poker.bat
```

### Manual
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Mac

### Automatic
```bash
chmod +x play_poker.sh
./setup.sh
```

### Manual
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```