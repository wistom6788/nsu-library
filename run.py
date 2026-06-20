"""
NSU Library Dashboard — Quick Start
Usage:
  开发模式: python run.py
  生产模式: python run.py --prod
"""
import sys
import uvicorn
from app.config import HOST, PORT

if __name__ == "__main__":
    is_prod = "--prod" in sys.argv
    mode = "PRODUCTION" if is_prod else "DEVELOPMENT"
    print(f"[START] NSU Library Dashboard ({mode})")
    print(f"        http://{HOST}:{PORT}")
    print(f"        Press Ctrl+C to stop\n")
    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        reload=not is_prod,
        workers=1 if not is_prod else 2,
    )
