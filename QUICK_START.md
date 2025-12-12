# Quick Start Guide

## Starting the Server

Since you're on macOS, use `python3` instead of `python`:

```bash
python3 app.py
```

Or use the start script:
```bash
./start.sh
```

## Accessing the Dashboard

Once the server starts, you'll see a message like:
```
📊 Dashboard: http://localhost:5001
```

Open that URL in your browser.

## If You Get "Command Not Found"

Make sure you're using `python3`:
```bash
python3 app.py
```

## If Port 5001 is Busy

Specify a different port:
```bash
python3 app.py 8080
```

Then access: `http://localhost:8080`

## Troubleshooting

1. **Server won't start**: Make sure Flask is installed:
   ```bash
   python3 -m pip install -r requirements.txt
   ```

2. **"This site can't be reached"**: 
   - Make sure the server is actually running (check terminal for "Running on..." message)
   - Try a different port if the default one is busy
   - Make sure you're using the correct URL (check what the server prints)

3. **Port already in use**: Use a different port:
   ```bash
   python3 app.py 3000
   ```








