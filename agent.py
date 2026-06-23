import os
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI()

@app.get("/")
async def read_index():
    return FileResponse('index.html')

# Zde bude zbytek tvého kódu pro JARVISE...

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("agent:app", host="0.0.0.0", port=port, log_level="info")
from fastapi.responses import FileResponse

@app.get("/")
async def read_index():
    return FileResponse('index.html')
import os
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse

# Tady vlož veškerý svůj původní kód (třídy, proměnné, logiku JARVISE)
# ... tvůj původní kód ...

app = FastAPI()

@app.get("/")
async def read_index():
    return FileResponse('index.html')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("agent:app", host="0.0.0.0", port=port, log_level="info")
