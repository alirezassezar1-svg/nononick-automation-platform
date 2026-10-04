#!/usr/bin/env python3
"""Manual webhook endpoint for triggering the content pipeline."""

import hashlib
import hmac
import os
import subprocess
import sys

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

load_dotenv()

app = FastAPI(title='Nononick Content Automation Webhook')
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'nononick-webhook-secret-change-this')


@app.get('/health')
def health():
    return {'status': 'ok'}


@app.post('/webhook/run')
async def trigger_pipeline(request: Request, x_webhook_signature: str = Header(default='')):
    body = await request.body()

    if WEBHOOK_SECRET and WEBHOOK_SECRET != 'nononick-webhook-secret-change-this':
        expected = hmac.new(WEBHOOK_SECRET.encode('utf-8'), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(x_webhook_signature, expected):
            raise HTTPException(status_code=401, detail='Invalid signature')

    result = subprocess.run([sys.executable, 'scripts/run_pipeline.py'], capture_output=True, text=True)
    return JSONResponse({
        'success': result.returncode == 0,
        'stdout': result.stdout,
        'stderr': result.stderr,
    })


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=int(os.getenv('WEBHOOK_PORT', '8000')))
